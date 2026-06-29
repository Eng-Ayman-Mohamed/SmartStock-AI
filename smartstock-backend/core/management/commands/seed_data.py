import argparse
import os
import random
from datetime import date, datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AgentRun, AuditLog
from apps.authentication.models import CustomUser
from apps.forecasting.models import ForecastResult, ReorderFlag
from apps.inventory.models import SKU, Category, Product, SalesRecord, StockLevel, Supplier
from apps.purchasing.models import PurchaseOrder as PurchasingPurchaseOrder

try:
    from faker import Faker

    fake = Faker()
except ImportError as err:
    raise CommandError('Faker is required. Install it with: pip install faker') from err


def aware_dt(**kwargs):
    return timezone.make_aware(fake.date_time_between(**kwargs))


BASE_COUNTS = {
    CustomUser: 50,
    Category: 15,
    Supplier: 20,
    Product: 200,
    SKU: 400,
    StockLevel: 400,
    SalesRecord: 8000,
    PurchasingPurchaseOrder: 500,
    ForecastResult: 4000,
    ReorderFlag: 800,
    AgentRun: 50,
    AuditLog: 2000,
}

SEED_ORDER = [
    CustomUser,
    Category,
    Supplier,
    Product,
    SKU,
    StockLevel,
    SalesRecord,
    PurchasingPurchaseOrder,
    ForecastResult,
    ReorderFlag,
    AgentRun,
    AuditLog,
]

REVERSE_ORDER = list(reversed(SEED_ORDER))


def truncate_all():
    for model in REVERSE_ORDER:
        model.objects.all().delete()


def seed_users(scale: int) -> list[CustomUser]:
    count = BASE_COUNTS[CustomUser] * scale
    emails = set()
    users = []
    managers = []

    DEV_USERS = [
        {
            'username': 'admin',
            'email': 'admin@smartstock.ai',
            'password': 'SmartStock2026!',
            'first_name': 'Dev',
            'last_name': 'Admin',
            'role': CustomUser.Role.ADMIN,
            'is_staff': True,
            'is_superuser': True,
        },
        {
            'username': 'manager',
            'email': 'manager@smartstock.ai',
            'password': 'Manager123!',
            'first_name': 'Dev',
            'last_name': 'Manager',
            'role': CustomUser.Role.MANAGER,
            'is_staff': True,
            'is_superuser': False,
        },
        {
            'username': 'viewer',
            'email': 'viewer@smartstock.ai',
            'password': 'Viewer123!',
            'first_name': 'Dev',
            'last_name': 'Viewer',
            'role': CustomUser.Role.VIEWER,
            'is_staff': True,
            'is_superuser': False,
        },
    ]

    for dev in DEV_USERS:
        user = CustomUser(
            username=dev['username'],
            email=dev['email'],
            password=make_password(dev['password']),
            first_name=dev['first_name'],
            last_name=dev['last_name'],
            role=dev['role'],
            is_active=True,
            email_verified=True,
            is_staff=dev['is_staff'],
            is_superuser=dev['is_superuser'],
            date_joined=aware_dt(start_date='-2y', end_date='-1d'),
        )
        emails.add(dev['email'])
        users.append(user)
        if dev['role'] in (CustomUser.Role.MANAGER, CustomUser.Role.ADMIN):
            managers.append(user)

    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f'{first_name.lower()}.{last_name.lower()}@smartstock.ai'
        while email in emails:
            email = (
                f'{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@smartstock.ai'
            )
        emails.add(email)

        role_weights = [0.6, 0.3, 0.1]
        role = random.choices(
            [CustomUser.Role.VIEWER, CustomUser.Role.MANAGER, CustomUser.Role.ADMIN],
            weights=role_weights,
        )[0]

        user = CustomUser(
            username=f'user_{i + 1}',
            email=email,
            password=make_password('password123'),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            date_joined=aware_dt(start_date='-2y', end_date='-1d'),
        )
        users.append(user)
        if role in (CustomUser.Role.MANAGER, CustomUser.Role.ADMIN):
            managers.append(user)

    CustomUser.objects.bulk_create(users, batch_size=500)
    return users, managers


def seed_categories(scale: int) -> list[Category]:
    count = BASE_COUNTS[Category] * scale
    names = set()
    categories = []

    for i in range(count):
        name = fake.unique.word().title()
        while name in names:
            name = fake.unique.word().title()
        names.add(name)

        categories.append(
            Category(
                name=name,
                description=fake.paragraph(nb_sentences=3),
                created_at=aware_dt(start_date='-3y', end_date='-30d'),
            )
        )

    Category.objects.bulk_create(categories, batch_size=100)
    return categories


def seed_suppliers(scale: int) -> list[Supplier]:
    count = BASE_COUNTS[Supplier] * scale
    suppliers = []

    for i in range(count):
        suppliers.append(
            Supplier(
                name=fake.company(),
                contact_email=fake.company_email(),
                contact_phone=fake.phone_number(),
                address=fake.address(),
                default_lead_time_days=random.choices(
                    [3, 5, 7, 10, 14, 21, 30],
                    weights=[0.1, 0.2, 0.3, 0.2, 0.1, 0.05, 0.05],
                )[0],
                is_active=random.random() < 0.9,
                created_at=aware_dt(start_date='-3y', end_date='-30d'),
            )
        )

    Supplier.objects.bulk_create(suppliers, batch_size=100)
    return suppliers


CATEGORY_ADJECTIVES = [
    'Premium',
    'Basic',
    'Pro',
    'Eco',
    'Ultra',
    'Smart',
    'Industrial',
    'Heavy-Duty',
    'Compact',
    'Portable',
    'Professional',
    'Standard',
    'Deluxe',
    'Essential',
    'Advanced',
]

CATEGORY_NOUNS = [
    'Widget',
    'Gadget',
    'Tool',
    'Component',
    'Device',
    'Part',
    'Accessory',
    'Module',
    'Assembly',
    'Fixture',
    'Instrument',
    'Appliance',
    'Unit',
    'Element',
    'Material',
    'Sensor',
    'Actuator',
    'Controller',
    'Valve',
    'Pump',
    'Filter',
    'Gauge',
    'Bracket',
    'Fastener',
    'Seal',
    'Gasket',
    'Bearing',
    'Spring',
    'Gear',
    'Pulley',
]

UNIT_OF_MEASURE = ['units', 'kg', 'meters', 'liters', 'boxes', 'pallets', 'pieces', 'dozens']


def seed_products(
    scale: int, categories: list[Category], suppliers: list[Supplier]
) -> list[Product]:
    count = BASE_COUNTS[Product] * scale
    products = []

    for i in range(count):
        adj = random.choice(CATEGORY_ADJECTIVES)
        noun = random.choice(CATEGORY_NOUNS)
        products.append(
            Product(
                name=f'{adj} {noun} Mk{random.randint(1, 5)}',
                description=fake.paragraph(nb_sentences=4),
                category=random.choice(categories) if categories else None,
                supplier=random.choice(suppliers) if suppliers else None,
                unit_price=round(random.uniform(1, 999), 2),
                unit_of_measure=random.choice(UNIT_OF_MEASURE),
                reorder_point=random.randint(5, 100),
                safety_stock=random.randint(0, 50),
                max_warehouse_capacity=random.randint(100, 10000),
                is_active=random.random() < 0.95,
                created_at=aware_dt(start_date='-3y', end_date='-30d'),
            )
        )

    Product.objects.bulk_create(products, batch_size=200)
    return products


def seed_skus(scale: int, products: list[Product]) -> list[SKU]:
    count = BASE_COUNTS[SKU] * scale
    codes = set()
    skus = []

    for i in range(count):
        product = random.choice(products)
        code = f'SKU-{product.id:04d}-{random.randint(1000, 9999)}'
        while code in codes:
            code = f'SKU-{product.id:04d}-{random.randint(1000, 9999)}'
        codes.add(code)

        skus.append(
            SKU(
                product=product,
                code=code,
                attributes={
                    'color': random.choice(
                        ['Red', 'Blue', 'Green', 'Black', 'White', 'Yellow', None]
                    ),
                    'size': random.choice(['S', 'M', 'L', 'XL', None]),
                    'variant': random.choice(['A', 'B', 'C', None]),
                },
                created_at=product.created_at + timedelta(days=random.randint(0, 30))
                if product.created_at
                else aware_dt(start_date='-2y', end_date='-30d'),
            )
        )

    SKU.objects.bulk_create(skus, batch_size=200)
    return skus


def seed_stock_levels(scale: int, skus: list[SKU]) -> list[StockLevel]:
    count = BASE_COUNTS[StockLevel] * scale
    levels = []

    for sku in skus[:count]:
        on_hand = random.randint(0, 1000)
        reserved = random.randint(0, min(on_hand, 100))
        levels.append(
            StockLevel(
                sku=sku,
                quantity_on_hand=on_hand,
                quantity_reserved=reserved,
                reorder_point=random.randint(5, 50),
                reorder_quantity=random.choice([25, 50, 100, 200, 500]),
            )
        )

    StockLevel.objects.bulk_create(levels, batch_size=200)
    return levels


def _seasonal_demand(
    base_demand: float, day_of_week: int, day_of_month: int, day_offset: int
) -> float:
    """Compute seasonal demand multiplier from baseline."""
    weekday_mult = 1.3 if day_of_week < 5 else 0.6
    monthly_mult = 1.1 if 8 <= day_of_month <= 20 else 0.9
    trend_mult = 1.0 + (day_offset / 365) * random.uniform(-0.15, 0.15)
    noise = random.gauss(1.0, 0.1)
    return base_demand * weekday_mult * monthly_mult * trend_mult * noise


def seed_sales_records(scale: int, skus: list[SKU]) -> dict[int, float]:
    """Seed sales with seasonal patterns. Returns avg daily demand per SKU."""
    count = BASE_COUNTS[SalesRecord] * scale
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=365)

    sku_base_demand = {sku.id: random.uniform(5, 50) for sku in skus}
    sku_total_sales: dict[int, float] = {sku.id: 0.0 for sku in skus}
    sku_days_with_sales: dict[int, int] = {sku.id: 0 for sku in skus}

    records = []
    existing = set()

    for _ in range(count):
        sku = random.choice(skus)
        record_date = fake.date_between(start_date=start_date, end_date=end_date)

        key = (sku.id, record_date)
        while key in existing:
            sku = random.choice(skus)
            record_date = fake.date_between(start_date=start_date, end_date=end_date)
            key = (sku.id, record_date)
        existing.add(key)

        day_offset = (record_date - start_date).days
        qty = max(
            0,
            int(
                _seasonal_demand(
                    sku_base_demand[sku.id],
                    record_date.weekday(),
                    record_date.day,
                    day_offset,
                )
            ),
        )

        records.append(SalesRecord(sku=sku, date=record_date, quantity_sold=qty))
        sku_total_sales[sku.id] += qty
        sku_days_with_sales[sku.id] += 1

    SalesRecord.objects.bulk_create(records, batch_size=500)

    avg_daily_demand = {}
    for sku in skus:
        days = max(sku_days_with_sales[sku.id], 1)
        avg_daily_demand[sku.id] = sku_total_sales[sku.id] / days
    return avg_daily_demand


PO_STATUS_WEIGHTS = {
    'draft': 0.05,
    'pending_approval': 0.10,
    'approved': 0.15,
    'sent': 0.10,
    'confirmed': 0.40,
    'rejected': 0.05,
    'cancelled': 0.05,
    'waiting_confirmation': 0.05,
    'email_sent': 0.03,
    'failed': 0.02,
}


def seed_purchase_orders(
    scale: int,
    skus: list[SKU],
    suppliers: list[Supplier],
    users: list[CustomUser],
    managers: list[CustomUser],
    stock_levels: list[StockLevel],
    avg_daily_demand: dict[int, float],
):
    count = BASE_COUNTS[PurchasingPurchaseOrder] * scale
    orders = []
    po_counter = 0

    for _ in range(count):
        po_counter += 1
        chosen_sku = random.choice(skus)
        quantity = random.choice([10, 25, 50, 100, 200, 500, 1000])
        unit_cost = round(random.uniform(1, 500), 2)
        total_cost = round(quantity * unit_cost, 2)
        status = random.choices(
            list(PO_STATUS_WEIGHTS.keys()),
            weights=list(PO_STATUS_WEIGHTS.values()),
        )[0]

        requested_by = random.choice(users) if users else None
        approved_by = None
        if status in ('approved', 'sent', 'confirmed', 'email_sent', 'waiting_confirmation'):
            if managers:
                approved_by = random.choice(managers)

        created = aware_dt(start_date='-1y', end_date='-1d')

        avg_demand = avg_daily_demand.get(chosen_sku.id, 15)
        lead_time = random.choice([7, 14, 21])
        predicted_demand = round(avg_demand * lead_time, 1)
        reasoning = (
            f'Reorder triggered: stock below predicted demand of '
            f'{predicted_demand} units over {lead_time}-day lead time.'
        )

        orders.append(
            PurchasingPurchaseOrder(
                sku=chosen_sku,
                supplier=random.choice(suppliers) if suppliers else None,
                quantity=quantity,
                total_cost=total_cost,
                status=status,
                requested_by=requested_by,
                approved_by=approved_by,
                agent_reasoning=reasoning,
                po_number=f'PO-{date.today().year}-{po_counter:05d}',
                notes=fake.paragraph(nb_sentences=2) if random.random() < 0.3 else '',
                created_at=created,
            )
        )

    PurchasingPurchaseOrder.objects.bulk_create(orders, batch_size=200)
    return orders


def seed_forecasts(scale: int, skus: list[SKU], avg_daily_demand: dict[int, float]):
    """Generate forecasts for next 90 days, correlated with actual sales."""
    forecasts = []
    today = date.today()
    existing = set()
    target_count = BASE_COUNTS[ForecastResult] * scale

    for sku in skus:
        base = avg_daily_demand.get(sku.id, 15)
        num_forecast_days = min(90, target_count // len(skus))

        for day_offset in range(1, num_forecast_days + 1):
            forecast_date = today + timedelta(days=day_offset)

            key = (sku.id, forecast_date)
            if key in existing:
                continue
            existing.add(key)

            growth = 1.0 + (day_offset / 90) * random.uniform(-0.05, 0.05)
            predicted = round(base * growth * random.uniform(0.85, 1.15), 1)
            lower = round(predicted * random.uniform(0.6, 0.85), 1)
            upper = round(predicted * random.uniform(1.15, 1.8), 1)

            data_points = random.randint(50, 300)
            mae = round(max(0.5, predicted * 0.1 * (300 / data_points)), 2)
            mape = round(max(1.0, mae / max(predicted, 1) * 100), 2)

            forecasts.append(
                ForecastResult(
                    sku=sku,
                    forecast_date=forecast_date,
                    predicted_quantity=predicted,
                    lower_bound=lower,
                    upper_bound=upper,
                    mae=mae,
                    mape=mape,
                    model_version='prophet-1.1.5',
                )
            )

            if len(forecasts) >= target_count:
                break
        if len(forecasts) >= target_count:
            break

    ForecastResult.objects.bulk_create(forecasts, batch_size=500)
    return forecasts


def seed_reorder_flags(
    scale: int,
    skus: list[SKU],
    stock_levels: list[StockLevel],
    avg_daily_demand: dict[int, float],
    purchase_orders: list[PurchasingPurchaseOrder],
):
    """Compute reorder flags from real stock + forecast conditions."""
    sku_stock = {sl.sku.id: sl for sl in stock_levels}
    sku_open_pos: dict[int, list] = {}
    for po in purchase_orders:
        if po.status not in ('rejected', 'cancelled', 'failed'):
            sku_open_pos.setdefault(po.sku_id, []).append(po)

    flags = []
    for sku in skus:
        sl = sku_stock.get(sku.id)
        if not sl:
            continue

        quantity_available = sl.quantity_on_hand - sl.quantity_reserved
        lead_time = sku.product.supplier.default_lead_time_days if sku.product.supplier else 7
        predicted_demand = round(avg_daily_demand.get(sku.id, 15) * lead_time, 1)
        safety_stock = sku.product.safety_stock

        reorder_required = quantity_available < predicted_demand + safety_stock
        if not reorder_required:
            continue

        open_pos = sku_open_pos.get(sku.id, [])
        has_open_po = len(open_pos) > 0
        open_po_id = open_pos[0].id if open_pos else None

        deficit = predicted_demand + safety_stock - quantity_available
        reasoning = (
            f'Stock level critically low: {quantity_available} units available, '
            f'{predicted_demand:.0f} predicted demand over {lead_time}-day lead time, '
            f'{safety_stock} safety stock required. Deficit of {deficit:.0f} units.'
        )

        status = random.choices(
            ['open', 'consumed', 'dismissed'],
            weights=[0.6, 0.25, 0.15],
        )[0]

        flags.append(
            ReorderFlag(
                sku=sku,
                quantity_available=quantity_available,
                total_predicted_demand=predicted_demand,
                safety_stock=safety_stock,
                lead_time_days=lead_time,
                forecast_days=lead_time,
                reorder_required=True,
                has_open_po=has_open_po,
                open_po_id=open_po_id,
                reasoning=reasoning,
                status=status,
            )
        )

    ReorderFlag.objects.bulk_create(flags, batch_size=200)
    return flags


def seed_agent_runs(scale: int):
    count = BASE_COUNTS[AgentRun] * scale
    agent_names = [
        'forecast-engine',
        'reorder-agent',
        'po-generator',
        'supplier-analyzer',
        'inventory-auditor',
        'nl-query-handler',
        'invoice-processor',
        'anomaly-detector',
    ]
    runs = []

    for _ in range(count):
        status = random.choices(
            ['pending', 'running', 'completed', 'failed'],
            weights=[0.05, 0.05, 0.8, 0.1],
        )[0]
        started_at = aware_dt(start_date='-7d', end_date='now')

        runs.append(
            AgentRun(
                agent_name=random.choice(agent_names),
                status=status,
                started_at=started_at if status != 'pending' else None,
                completed_at=started_at + timedelta(minutes=random.randint(1, 30))
                if status == 'completed'
                else None,
                error_message=fake.sentence() if status == 'failed' else '',
            )
        )

    AgentRun.objects.bulk_create(runs, batch_size=100)
    return runs


AUDIT_EVENTS_POOL = [
    'USER_LOGIN',
    'PO_CREATED',
    'PO_APPROVED',
    'PO_REJECTED',
    'PO_SENT',
    'STOCK_ADJUSTED',
    'PRODUCT_CREATED',
    'PRODUCT_UPDATED',
    'INVOICE_CONFIRMED',
    'INVOICE_REJECTED',
    'AI_RAG_QUERY',
    'AGENT_RUN_COMPLETED',
]
AUDIT_EVENT_WEIGHTS = [
    0.25,
    0.08,
    0.06,
    0.04,
    0.04,
    0.1,
    0.08,
    0.08,
    0.05,
    0.03,
    0.12,
    0.07,
]

ENTITY_TYPES = [
    'PurchaseOrder',
    'User',
    'Product',
    'SKU',
    'StockLevel',
    'ReorderFlag',
    'AgentRun',
]


def seed_audit_logs(scale: int, users: list[CustomUser]):
    count = BASE_COUNTS[AuditLog] * scale
    logs = []

    for _ in range(count):
        logs.append(
            AuditLog(
                event=random.choices(AUDIT_EVENTS_POOL, weights=AUDIT_EVENT_WEIGHTS)[0],
                entity_type=random.choice(ENTITY_TYPES),
                entity_id=random.randint(1, 500),
                user=random.choice(users) if users and random.random() < 0.7 else None,
                ip_address=fake.ipv4() if random.random() < 0.9 else None,
                data_snapshot={'key': fake.word(), 'value': fake.word()},
                timestamp=aware_dt(start_date='-1y', end_date='now'),
            )
        )

    AuditLog.objects.bulk_create(logs, batch_size=500)
    return logs


class Command(BaseCommand):
    help = 'Seed the database with realistic development data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--scale',
            type=int,
            default=1,
            help='Scale factor (default: 1). Multiplies base row counts.',
        )
        parser.add_argument(
            '--truncate',
            action=argparse.BooleanOptionalAction,
            default=True,
            help='Truncate all tables before seeding (default: True). Use --no-truncate to skip.',
        )
        parser.add_argument(
            '--validate',
            action=argparse.BooleanOptionalAction,
            default=True,
            help='Run validation queries after seeding (default: True). Use --no-validate to skip.',
        )
        parser.add_argument(
            '--skip-agent-runs',
            action='store_true',
            default=False,
            help='Skip seeding AgentRun records. Production data comes from real agent executions.',
        )

    def handle(self, *args, **options):
        settings_module = os.environ.get('DJANGO_SETTINGS_MODULE', '')
        if 'production' in settings_module:
            raise CommandError(
                'seed_data cannot be run in production. '
                'Use this command only in development or test environments.'
            )

        scale = options['scale']
        truncate = options.get('truncate', True)
        skip_agent_runs = options.get('skip_agent_runs', False)

        if scale < 1 or scale > 100:
            raise CommandError('Scale must be between 1 and 100')

        self.stdout.write(f'Seeding database with scale={scale}')
        self.stdout.write(f'  Users:       {BASE_COUNTS[CustomUser] * scale}')
        self.stdout.write(f'  Categories:  {BASE_COUNTS[Category] * scale}')
        self.stdout.write(f'  Suppliers:   {BASE_COUNTS[Supplier] * scale}')
        self.stdout.write(f'  Products:    {BASE_COUNTS[Product] * scale}')
        self.stdout.write(f'  SKUs:        {BASE_COUNTS[SKU] * scale}')
        self.stdout.write(f'  StockLevels: {BASE_COUNTS[StockLevel] * scale}')
        self.stdout.write(f'  SalesRecs:   {BASE_COUNTS[SalesRecord] * scale}')
        self.stdout.write(f'  POs:         {BASE_COUNTS[PurchasingPurchaseOrder] * scale}')
        self.stdout.write(f'  Forecasts:   {BASE_COUNTS[ForecastResult] * scale}')
        self.stdout.write('  ReorderFlags: computed from stock + forecast')
        self.stdout.write(f'  AgentRuns:   {BASE_COUNTS[AgentRun] * scale}')
        self.stdout.write(f'  AuditLogs:   {BASE_COUNTS[AuditLog] * scale}')

        start = datetime.now()

        with transaction.atomic():
            if truncate:
                self.stdout.write('Truncating existing data...')
                truncate_all()

            self.stdout.write('Seeding users...')
            users, managers = seed_users(scale)

            self.stdout.write('Seeding categories...')
            categories = seed_categories(scale)

            self.stdout.write('Seeding suppliers...')
            suppliers = seed_suppliers(scale)

            self.stdout.write('Seeding products...')
            products = seed_products(scale, categories, suppliers)

            self.stdout.write('Seeding SKUs...')
            skus = seed_skus(scale, products)

            self.stdout.write('Seeding stock levels...')
            stock_levels = seed_stock_levels(scale, skus)

            self.stdout.write('Seeding sales records (seasonal + trend)...')
            avg_daily_demand = seed_sales_records(scale, skus)

            self.stdout.write('Seeding purchase orders...')
            purchase_orders = seed_purchase_orders(
                scale, skus, suppliers, users, managers, stock_levels, avg_daily_demand
            )

            self.stdout.write('Seeding forecasts (correlated with sales)...')
            seed_forecasts(scale, skus, avg_daily_demand)

            self.stdout.write('Seeding reorder flags (computed from stock + forecast)...')
            seed_reorder_flags(scale, skus, stock_levels, avg_daily_demand, purchase_orders)

            if not skip_agent_runs:
                self.stdout.write('Seeding agent runs...')
                seed_agent_runs(scale)
            else:
                self.stdout.write(
                    'Skipping agent runs (use real agent executions for dashboard data).'
                )

            self.stdout.write('Seeding audit logs...')
            seed_audit_logs(scale, users)

        elapsed = datetime.now() - start
        self.stdout.write(self.style.SUCCESS(f'Seeding complete in {elapsed.total_seconds():.2f}s'))

        if options.get('validate', True):
            self.validate()

    def validate(self):
        self.stdout.write()
        self.stdout.write('Validating seed data integrity...')
        checks = []
        all_models = [
            CustomUser,
            Category,
            Supplier,
            Product,
            SKU,
            StockLevel,
            SalesRecord,
            PurchasingPurchaseOrder,
            ForecastResult,
            ReorderFlag,
            AgentRun,
            AuditLog,
        ]

        for model in all_models:
            count = model.objects.count()
            expected = BASE_COUNTS.get(model, 0)
            status_msg = '✓' if count > 0 else '✗'
            checks.append((model.__name__, count, expected, status_msg))

        header = f'{"Model":<25} {"Count":>8} {"Expected":>10}  Status'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))
        all_ok = True
        for name, count, expected, status_msg in checks:
            line = f'{name:<25} {count:>8} {expected:>10}  {status_msg}'
            self.stdout.write(line)
            if count == 0:
                all_ok = False

        fk_checks = [
            ('SalesRecord → SKU', SalesRecord, 'sku_id', SKU),
            ('PurchaseOrder → SKU', PurchasingPurchaseOrder, 'sku_id', SKU),
            ('PurchaseOrder → Supplier', PurchasingPurchaseOrder, 'supplier_id', Supplier),
            ('ForecastResult → SKU', ForecastResult, 'sku_id', SKU),
            ('ReorderFlag → SKU', ReorderFlag, 'sku_id', SKU),
            ('AuditLog → User', AuditLog, 'user_id', CustomUser),
        ]

        self.stdout.write()
        self.stdout.write('Foreign key integrity checks:')
        for label, child_model, fk_field, parent_model in fk_checks:
            orphans = (
                child_model.objects.filter(**{f'{fk_field}__isnull': False})
                .exclude(**{f'{fk_field}__in': parent_model.objects.values_list('pk', flat=True)})
                .count()
            )
            status_msg = '✓' if orphans == 0 else '✗'
            self.stdout.write(f'  {status_msg} {label}: {orphans} orphans')
            if orphans > 0:
                all_ok = False

        if all_ok:
            self.stdout.write(self.style.SUCCESS('✓ All validation checks passed'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Some checks failed — review above'))
