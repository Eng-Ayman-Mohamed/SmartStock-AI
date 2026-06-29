import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.utils import timezone

from ai.agents.decision_agent import DecisionAgent
from ai.agents.po_from_flag_creator import POFromFlagCreator
from apps.audit.models import AgentRun
from apps.forecasting.models import ReorderFlag

logger = logging.getLogger(__name__)


class AgentPipelineOrchestrator:
    def __init__(self, system_user_id: int | None = None):
        self.system_user_id = system_user_id
        self.decision_agent = DecisionAgent()
        self.po_creator = POFromFlagCreator(system_user_id=system_user_id)

    def run(self) -> dict:
        logger.info('AgentPipelineOrchestrator: starting daily run')

        run_record = AgentRun.objects.create(
            agent_name='agent_pipeline_orchestrator',
            status='running',
            started_at=timezone.now(),
        )

        try:
            # Step 1: Forecast all active SKUs
            forecast_result = self._run_forecast_step()
            logger.info('Forecast step complete: %s', forecast_result)

            # Step 2: Use the SKU IDs from dispatched forecasts
            # (forecasts generate future dates, so querying forecast_date=today returns nothing)
            sku_ids = forecast_result.get('sku_ids', [])
            if not sku_ids:
                logger.info('No SKUs to evaluate, skipping decision step')
                run_record.status = 'completed'
                run_record.completed_at = timezone.now()
                run_record.save(update_fields=['status', 'completed_at'])
                return {
                    'forecast': forecast_result,
                    'decision': {'skus_processed': 0, 'reorder_flags_created': 0, 'errors': []},
                    'po_creation': {'created': 0, 'skipped_no_supplier': 0, 'failed': 0, 'errors': []},
                }

            # Step 3: Run DecisionAgent per SKU (parallelized)
            decision_result = self._run_decision_step(sku_ids)
            logger.info('Decision step complete: %s', decision_result)

            # Step 4: Read OPEN flags and create POs
            po_result = self._run_po_creation_step()
            logger.info('PO creation step complete: %s', po_result)

            output = {
                'forecast': forecast_result,
                'decision': decision_result,
                'po_creation': po_result,
            }

            run_record.status = 'completed'
            run_record.completed_at = timezone.now()
            run_record.output_data = output
            run_record.save(update_fields=['status', 'completed_at', 'output_data'])

            return output
        except Exception:
            logger.exception('AgentPipelineOrchestrator run failed')
            run_record.status = 'failed'
            run_record.completed_at = timezone.now()
            run_record.save(update_fields=['status', 'completed_at'])
            raise

    def _run_forecast_step(self) -> dict:
        from apps.inventory.models import SKU

        sku_ids = list(SKU.objects.filter(product__is_active=True).values_list('id', flat=True))

        if not sku_ids:
            return {'dispatched': 0}

        from celery import group

        from .tasks import run_forecast_single_sku

        logger.info('Dispatching %d parallel forecast tasks', len(sku_ids))
        job = group(run_forecast_single_sku.s(sku_id) for sku_id in sku_ids)
        result = job.apply_async()

        try:
            forecast_results = result.get(timeout=600, propagate=False)
            completed = sum(
                1
                for r in forecast_results
                if r is not None and not isinstance(r, Exception)
            )
            logger.info(
                'Forecast tasks: %d/%d completed', completed, len(sku_ids)
            )
        except Exception:
            logger.warning('Some forecast tasks timed out; continuing with partial results')

        from django.core.cache import cache

        try:
            cache.delete_pattern('forecast_dashboard_*')
        except Exception:
            logger.warning(
                'Failed to invalidate forecast dashboard cache', exc_info=True
            )

        return {'dispatched': len(sku_ids), 'group_id': str(result.id), 'sku_ids': sku_ids}

    def _run_decision_step(self, sku_ids: list[int]) -> dict:
        results = []

        def _evaluate(sku_id: int) -> dict:
            agent = DecisionAgent()
            return agent.evaluate_sku(sku_id)

        with ThreadPoolExecutor(max_workers=min(5, len(sku_ids) or 1)) as executor:
            futures = {
                executor.submit(_evaluate, sku_id): sku_id for sku_id in sku_ids
            }
            for future in as_completed(futures):
                sku_id = futures[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.exception('DecisionAgent.evaluate_sku failed for SKU %s', sku_id)
                    results.append({'sku_id': sku_id, 'error': str(e)})

        return {
            'skus_processed': len(results),
            'reorder_flags_created': sum(
                1 for r in results if isinstance(r, dict) and r.get('reorder_flag_id')
            ),
            'errors': [r for r in results if 'error' in r],
        }

    def _run_po_creation_step(self) -> dict:
        open_flags = ReorderFlag.objects.filter(
            status=ReorderFlag.Status.OPEN,
            reorder_required=True,
            has_open_po=False,
        ).select_related('sku__product__supplier')

        return self.po_creator.process_flags(open_flags)
