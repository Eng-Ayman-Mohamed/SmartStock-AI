import random
from datetime import date, datetime, timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.audit.models import AgentRun, AuditLog
from apps.authentication.models import CustomUser
from apps.forecasting.models import ForecastResult, ReorderFlag
from apps.ingestion.models import Document, DocumentChunk, InvoiceScan
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
    Document: 30,
    DocumentChunk: 600,
    InvoiceScan: 100,
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
    Document,
    DocumentChunk,
    InvoiceScan,
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


def seed_sales_records(scale: int, skus: list[SKU]):
    count = BASE_COUNTS[SalesRecord] * scale
    records = []
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=365)

    sku_popularity = {sku.id: random.expovariate(1 / 3) for sku in skus}

    existing = set()

    for _ in range(count):
        sku = random.choices(skus, weights=[sku_popularity[s.id] for s in skus], k=1)[0]
        record_date = fake.date_between(start_date=start_date, end_date=end_date)

        key = (sku.id, record_date)
        while key in existing:
            sku = random.choices(skus, weights=[sku_popularity[s.id] for s in skus], k=1)[0]
            record_date = fake.date_between(start_date=start_date, end_date=end_date)
            key = (sku.id, record_date)
        existing.add(key)

        records.append(
            SalesRecord(
                sku=sku,
                date=record_date,
                quantity_sold=max(0, int(random.gauss(20, 8))),
            )
        )

    SalesRecord.objects.bulk_create(records, batch_size=500)
    return records


PO_STATUS_WEIGHTS = {
    'draft': 0.1,
    'pending_approval': 0.1,
    'approved': 0.2,
    'sent': 0.1,
    'confirmed': 0.3,
    'rejected': 0.1,
    'cancelled': 0.1,
}


def seed_purchase_orders(
    scale: int,
    skus: list[SKU],
    suppliers: list[Supplier],
    users: list[CustomUser],
    managers: list[CustomUser],
):
    count = BASE_COUNTS[PurchasingPurchaseOrder] * scale
    orders = []

    for _ in range(count):
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
        if status in ('approved', 'sent', 'confirmed', 'rejected') and managers:
            approved_by = random.choice(managers)

        created = aware_dt(start_date='-1y', end_date='-1d')
        orders.append(
            PurchasingPurchaseOrder(
                sku=chosen_sku,
                supplier=random.choice(suppliers) if suppliers else None,
                quantity=quantity,
                total_cost=total_cost,
                status=status,
                requested_by=requested_by,
                approved_by=approved_by,
                notes=fake.paragraph(nb_sentences=2) if random.random() < 0.3 else '',
                created_at=created,
            )
        )

    PurchasingPurchaseOrder.objects.bulk_create(orders, batch_size=200)
    return orders


def seed_forecasts(scale: int, skus: list[SKU]):
    count = BASE_COUNTS[ForecastResult] * scale
    forecasts = []
    end_date = date.today() + timedelta(days=90)
    start_date = date.today() - timedelta(days=30)

    existing = set()

    for _ in range(count):
        sku = random.choice(skus)
        forecast_date = fake.date_between(start_date=start_date, end_date=end_date)

        key = (sku.id, forecast_date)
        while key in existing:
            sku = random.choice(skus)
            forecast_date = fake.date_between(start_date=start_date, end_date=end_date)
            key = (sku.id, forecast_date)
        existing.add(key)

        predicted = round(random.uniform(5, 200), 1)
        forecasts.append(
            ForecastResult(
                sku=sku,
                forecast_date=forecast_date,
                predicted_quantity=predicted,
                lower_bound=round(predicted * random.uniform(0.5, 0.85), 1),
                upper_bound=round(predicted * random.uniform(1.15, 1.8), 1),
                mae=round(random.uniform(1, 15), 2),
                mape=round(random.uniform(2, 25), 2),
                model_version='prophet-1.1.5',
            )
        )

    ForecastResult.objects.bulk_create(forecasts, batch_size=500)
    return forecasts


def seed_reorder_flags(scale: int, skus: list[SKU]):
    count = BASE_COUNTS[ReorderFlag] * scale
    flags = []

    for sku in random.choices(skus, k=count):
        on_hand = random.randint(0, 200)
        predicted_demand = round(random.uniform(10, 500), 1)
        flags.append(
            ReorderFlag(
                sku=sku,
                quantity_available=on_hand,
                total_predicted_demand=predicted_demand,
                safety_stock=random.randint(0, 50),
                lead_time_days=random.choice([3, 5, 7, 10, 14]),
                forecast_days=random.choice([7, 14, 30, 90]),
                reorder_required=on_hand < predicted_demand,
                has_open_po=random.random() < 0.3,
                open_po_id=random.randint(1, 500) if random.random() < 0.2 else None,
                reasoning=fake.paragraph(nb_sentences=3),
                status=random.choices(
                    ['open', 'consumed', 'dismissed'],
                    weights=[0.5, 0.3, 0.2],
                )[0],
            )
        )

    ReorderFlag.objects.bulk_create(flags, batch_size=200)
    return flags


def seed_invoice_scans(scale: int, users: list[CustomUser]):
    count = BASE_COUNTS[InvoiceScan] * scale
    scans = []

    for i in range(count):
        user = random.choice(users)
        ext = random.choice(['.pdf', '.jpg', '.png'])
        filename = f'invoice_{i + 1}{ext}'
        status = random.choices(
            ['pending', 'extracted', 'partial', 'failed', 'confirmed', 'rejected'],
            weights=[0.1, 0.3, 0.15, 0.05, 0.3, 0.1],
        )[0]
        extracted = {
            'invoice_number': f'INV-{fake.random_number(digits=6)}',
            'vendor': fake.company(),
            'total': round(random.uniform(100, 50000), 2),
            'date': str(fake.date_between(start_date='-6M', end_date='today')),
        }

        scans.append(
            InvoiceScan(
                uploaded_by=user,
                original_filename=filename,
                content_type=f'image/{ext[1:]}' if ext in ('.jpg', '.png') else 'application/pdf',
                file_size=random.randint(100000, 10000000),
                status=status,
                extracted_data=extracted,
                confidence={
                    'invoice_number': round(random.uniform(0.7, 1.0), 2),
                    'vendor': round(random.uniform(0.6, 1.0), 2),
                    'total': round(random.uniform(0.5, 1.0), 2),
                },
                missing_fields=random.sample(
                    ['vendor', 'date', 'total', 'line_items'],
                    k=random.choices([0, 1, 2, 3], weights=[0.5, 0.3, 0.15, 0.05])[0],
                ),
                failure_reason=fake.sentence() if status == 'failed' else '',
                confirmed_data=extracted if status == 'confirmed' else {},
                is_confirmed=status == 'confirmed',
                confirmed_at=aware_dt(start_date='-30d', end_date='-1d')
                if status == 'confirmed'
                else None,
                rejected_at=aware_dt(start_date='-30d', end_date='-1d')
                if status == 'rejected'
                else None,
            )
        )

    InvoiceScan.objects.bulk_create(scans, batch_size=100)
    return scans


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


DOC_TYPES_POOL = ['policy', 'contract', 'procedure', 'specification']
DOC_TYPE_WEIGHTS = [0.3, 0.3, 0.2, 0.2]

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
    'InvoiceScan',
    'ReorderFlag',
    'AgentRun',
]


def seed_documents(scale: int, users: list[CustomUser]) -> list[Document]:
    count = BASE_COUNTS[Document] * scale
    documents = []

    for i in range(count):
        doc_type = random.choices(DOC_TYPES_POOL, weights=DOC_TYPE_WEIGHTS)[0]
        ext = random.choice(['.pdf', '.docx', '.txt'])
        filename = f'{doc_type}_{i + 1}{ext}'

        uploaded_by = random.choice(users) if users and random.random() < 0.8 else None

        documents.append(
            Document(
                filename=filename,
                original_filename=filename,
                doc_type=doc_type,
                file_size=random.randint(50000, 5000000),
                total_chunks=random.randint(5, 50),
                cloudinary_url=f'https://res.cloudinary.com/smartstock/raw/upload/{filename}',
                uploaded_by=uploaded_by,
                ingested_at=aware_dt(start_date='-6M', end_date='-1d')
                if random.random() < 0.9
                else None,
                is_active=random.random() < 0.95,
            )
        )

    Document.objects.bulk_create(documents, batch_size=100)
    return documents


def seed_document_chunks(scale: int, documents: list[Document]):
    count = BASE_COUNTS[DocumentChunk] * scale
    chunks = []

    for _ in range(count):
        doc = random.choice(documents) if documents else None
        chunks.append(
            DocumentChunk(
                chunk_text=fake.paragraph(nb_sentences=10),
                source_document=doc.filename if doc else 'unknown.pdf',
                page_number=random.randint(1, 50),
                metadata={'heading': fake.sentence(nb_words=4)},
                document=doc,
            )
        )

    DocumentChunk.objects.bulk_create(chunks, batch_size=200)
    return chunks


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
            action='store_true',
            default=True,
            help='Truncate all tables before seeding (default: True).',
        )
        parser.add_argument(
            '--validate',
            action='store_true',
            default=True,
            help='Run validation queries after seeding (default: True).',
        )

    def handle(self, *args, **options):
        scale = options['scale']
        truncate = options.get('truncate', True)

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
        self.stdout.write(f'  ReorderFlags:{BASE_COUNTS[ReorderFlag] * scale}')
        self.stdout.write(f'  Documents:   {BASE_COUNTS[Document] * scale}')
        self.stdout.write(f'  Chunks:      {BASE_COUNTS[DocumentChunk] * scale}')
        self.stdout.write(f'  InvoiceScans:{BASE_COUNTS[InvoiceScan] * scale}')
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
            seed_stock_levels(scale, skus)

            self.stdout.write('Seeding sales records...')
            seed_sales_records(scale, skus)

            self.stdout.write('Seeding purchase orders...')
            seed_purchase_orders(scale, skus, suppliers, users, managers)

            self.stdout.write('Seeding forecasts...')
            seed_forecasts(scale, skus)

            self.stdout.write('Seeding reorder flags...')
            seed_reorder_flags(scale, skus)

            self.stdout.write('Seeding documents...')
            docs = seed_documents(scale, users)

            self.stdout.write('Seeding document chunks...')
            seed_document_chunks(scale, docs)

            self.stdout.write('Seeding invoice scans...')
            seed_invoice_scans(scale, users)

            self.stdout.write('Seeding agent runs...')
            seed_agent_runs(scale)

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
            Document,
            DocumentChunk,
            InvoiceScan,
            AgentRun,
            AuditLog,
        ]

        for model in all_models:
            count = model.objects.count()
            expected = BASE_COUNTS.get(model, 0)
            status = '✓' if count > 0 else '✗'
            checks.append((model.__name__, count, expected, status))

        header = f'{"Model":<25} {"Count":>8} {"Expected":>10}  Status'
        self.stdout.write(header)
        self.stdout.write('-' * len(header))
        all_ok = True
        for name, count, expected, status in checks:
            line = f'{name:<25} {count:>8} {expected:>10}  {status}'
            self.stdout.write(line)
            if count == 0:
                all_ok = False

        fk_checks = [
            ('SalesRecord → SKU', SalesRecord, 'sku_id', SKU),
            ('PurchaseOrder → SKU', PurchasingPurchaseOrder, 'sku_id', SKU),
            ('PurchaseOrder → Supplier', PurchasingPurchaseOrder, 'supplier_id', Supplier),
            ('ForecastResult → SKU', ForecastResult, 'sku_id', SKU),
            ('ReorderFlag → SKU', ReorderFlag, 'sku_id', SKU),
            ('DocumentChunk → Document', DocumentChunk, 'document_id', Document),
            ('InvoiceScan → User', InvoiceScan, 'uploaded_by_id', CustomUser),
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
            status = '✓' if orphans == 0 else '✗'
            self.stdout.write(f'  {status} {label}: {orphans} orphans')
            if orphans > 0:
                all_ok = False

        if all_ok:
            self.stdout.write(self.style.SUCCESS('✓ All validation checks passed'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Some checks failed — review above'))
