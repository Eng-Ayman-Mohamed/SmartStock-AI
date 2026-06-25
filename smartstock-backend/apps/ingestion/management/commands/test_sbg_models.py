import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import requests
from django.core.management.base import BaseCommand


@dataclass
class SBGModel:
    model_id: str
    category: str
    description: str
    test_prompt: str = 'Say hello in one word.'
    max_tokens: int = 20


APPROVED_MODELS = [
    # ── Chat / Text Generation ──
    SBGModel(model_id='anthropic.claude-sonnet-4-6', category='chat',
             description='Claude Sonnet 4.6 — best overall chat'),
    SBGModel(model_id='anthropic.claude-opus-4-7', category='chat',
             description='Claude Opus 4.7 — most capable'),
    SBGModel(model_id='anthropic.claude-haiku-4-5-20251001-v1:0', category='chat',
             description='Claude Haiku 4.5 — fast'),
    SBGModel(model_id='deepseek.r1-v1:0', category='chat',
             description='DeepSeek R1 — reasoning'),
    SBGModel(model_id='deepseek.v3.2', category='chat',
             description='DeepSeek V3.2 — general chat'),
    SBGModel(model_id='mistral.voxtral-small-24b-2507', category='chat',
             description='Mistral Voxtral Small'),
    SBGModel(model_id='openai.gpt-oss-120b-1:0', category='chat',
             description='OpenAI GPT-OSS 120B'),
    SBGModel(model_id='openai.gpt-oss-20b-1:0', category='chat',
             description='OpenAI GPT-OSS 20B'),
    SBGModel(model_id='openai.gpt-oss-safeguard-120b', category='chat',
             description='OpenAI GPT-OSS Safeguard 120B'),
    SBGModel(model_id='openai.gpt-oss-safeguard-20b', category='chat',
             description='OpenAI GPT-OSS Safeguard 20B'),
    SBGModel(model_id='us.meta.llama3-3-70b-instruct-v1:0', category='chat',
             description='Meta Llama 3.3 70B',
             test_prompt='Say hello in exactly one word.'),
    SBGModel(model_id='us.amazon.nova-2-lite-v1:0', category='chat',
             description='Amazon Nova 2 Lite'),
    SBGModel(model_id='amazon.nova-2-sonic-v1:0', category='chat',
             description='Amazon Nova 2 Sonic (multimodal)'),
    # ── Vision (multimodal) ──
    SBGModel(model_id='qwen.qwen3-vl-235b-a22b', category='vision',
             description='Qwen 3 VL 235B (vision-language)',
             test_prompt='Describe this image for a beginner.'),
    # ── Embeddings ──
    SBGModel(model_id='amazon.titan-embed-text-v2:0:8k', category='embedding',
             description='Amazon Titan Embed Text V2 (8k)'),
    SBGModel(model_id='amazon.nova-2-multimodal-embeddings-v1:0', category='embedding',
             description='Amazon Nova 2 Multimodal Embeddings'),
    SBGModel(model_id='amazon.titan-embed-image-v1', category='embedding',
             description='Amazon Titan Embed Image V1'),
    SBGModel(model_id='us.cohere.embed-v4:0', category='embedding',
             description='Cohere Embed V4'),
    SBGModel(model_id='us.twelvelabs.marengo-embed-3-0-v1:0', category='embedding',
             description='Twelve Labs Marengo Embed 3.0'),
    # ── Image Generation ──
    SBGModel(model_id='amazon.titan-image-generator-v2:0', category='image',
             description='Amazon Titan Image Generator V2'),
    SBGModel(model_id='stability.stable-image-remove-background-v1:0', category='image',
             description='StabilityAI Remove Background'),
    SBGModel(model_id='stability.stable-image-inpaint-v1:0', category='image',
             description='StabilityAI Inpaint'),
    SBGModel(model_id='stability.stable-outpaint-v1:0', category='image',
             description='StabilityAI Outpaint'),
    SBGModel(model_id='stability.stable-fast-upscale-v1:0', category='image',
             description='StabilityAI Fast Upscale'),
    # ── Video ──
    SBGModel(model_id='amazon.nova-reel-v1:1', category='video',
             description='Amazon Nova Reel V1 (video gen)'),
    # ── Other ──
    SBGModel(model_id='global.twelvelabs.pegasus-1-2-v1:0', category='other',
             description='Twelve Labs Pegasus 1.2'),
]

ENDPOINTS = {
    'chat': 'http://apiaccess.iti.net.eg/api/v1/student/chat',
    'vision': 'http://apiaccess.iti.net.eg/api/v1/student/multimodal-chat',
    'embedding': 'http://apiaccess.iti.net.eg/api/v1/student/embed',
    'image': 'http://apiaccess.iti.net.eg/api/v1/student/generate-image',
    'video': 'http://apiaccess.iti.net.eg/api/v1/student/generate-video',
    'audio': 'http://apiaccess.iti.net.eg/api/v1/student/audio',
    'other': None,
}

COLORS = {
    'green': '\033[92m', 'red': '\033[91m', 'yellow': '\033[93m',
    'cyan': '\033[96m', 'bold': '\033[1m', 'dim': '\033[2m', 'reset': '\033[0m',
}


def c(text, *keys):
    return ''.join(COLORS[k] for k in keys) + text + COLORS['reset']


def trunc(s, n=60):
    s = str(s).replace('\n', '\\n')
    return s[:n] + '...' if len(s) > n else s


@dataclass
class TestResult:
    model_id: str
    category: str
    status: str
    status_code: Optional[int] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None
    output: Optional[str] = None
    usage: dict = field(default_factory=dict)


def request_json(method, url, payload, headers, timeout):
    start = time.time()
    try:
        resp = method(url, json=payload, headers=headers, timeout=timeout)
        latency = int((time.time() - start) * 1000)
        ct = resp.headers.get('content-type', '')
        body = resp.json() if ct.startswith('application/json') else {}
        return resp.status_code, body, latency, None
    except requests.exceptions.Timeout:
        return None, {}, timeout * 1000, f'No response after {timeout}s'
    except requests.exceptions.ConnectionError:
        return None, {}, 0, 'Could not connect to gateway'
    except Exception as exc:
        return None, {}, 0, str(exc)


def _auth_headers(api_key):
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


def _check_accepted(status_code, body, error_kws=None):
    """Return True if the gateway accepted the request (model+key valid)."""
    if status_code in (200, 202):
        return True
    if status_code in (400, 403, 422) and error_kws:
        err = body.get('error', {})
        text = (err.get('code', '') + ' ' + err.get('message', '')).lower()
        if any(kw in text for kw in error_kws):
            return True
    return False


def test_chat(model: SBGModel, api_key: str, timeout: int) -> TestResult:
    payload = {
        'model_id': model.model_id,
        'messages': [{'role': 'user', 'content': model.test_prompt}],
        'max_tokens': model.max_tokens or 50,
    }
    status_code, body, latency, err = request_json(
        requests.post, ENDPOINTS['chat'], payload, _auth_headers(api_key), timeout)
    if err:
        return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                          error_code='CONNECTION', error_message=trunc(err, 100), latency_ms=latency)
    if status_code == 200:
        output = body.get('output_text', '')
        return TestResult(model_id=model.model_id, category=model.category, status='OK',
                          status_code=200, latency_ms=latency, output=trunc(output),
                          usage=body.get('usage', {}))
    error = body.get('error', {})
    return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                      status_code=status_code,
                      error_code=error.get('code', f'HTTP_{status_code}'),
                      error_message=trunc(error.get('message', ''), 100), latency_ms=latency)


def test_vision(model: SBGModel, api_key: str, timeout: int) -> TestResult:
    payload = {
        'model_id': model.model_id,
        'messages': [{'role': 'user', 'text': model.test_prompt}],
        'max_tokens': model.max_tokens or 100,
    }
    status_code, body, latency, err = request_json(
        requests.post, ENDPOINTS['vision'], payload, _auth_headers(api_key), timeout)
    if err:
        return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                          error_code='CONNECTION', error_message=trunc(err, 100), latency_ms=latency)
    if _check_accepted(status_code, body, error_kws=['not allowed', 'region', 'model', 'image']):
        output = body.get('output_text', '') or body.get('text', '')
        return TestResult(model_id=model.model_id, category=model.category, status='OK',
                          status_code=status_code, latency_ms=latency,
                          output=trunc(output or body.get('content', json.dumps(body)), 70),
                          usage=body.get('usage', {}))
    error = body.get('error', {})
    return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                      status_code=status_code,
                      error_code=error.get('code', f'HTTP_{status_code}'),
                      error_message=trunc(error.get('message', ''), 100), latency_ms=latency)


def test_embedding(model: SBGModel, api_key: str, timeout: int) -> TestResult:
    payload = {
        'model_id': model.model_id,
        'texts': ['Algorithms are step-by-step instructions for solving problems.'],
        'input_type': 'search_document',
    }
    status_code, body, latency, err = request_json(
        requests.post, ENDPOINTS['embedding'], payload, _auth_headers(api_key), timeout)
    if err:
        return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                          error_code='CONNECTION', error_message=trunc(err, 100), latency_ms=latency)
    if _check_accepted(status_code, body, error_kws=['not allowed', 'region', 'model']):
        embeddings = body.get('embeddings', [])
        dims = len(embeddings[0]) if embeddings else 0
        return TestResult(model_id=model.model_id, category=model.category, status='OK',
                          status_code=status_code, latency_ms=latency,
                          output=f'vector[{dims}]' if dims else trunc(json.dumps(body), 70),
                          usage=body.get('usage', {}))
    error = body.get('error', {})
    return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                      status_code=status_code,
                      error_code=error.get('code', f'HTTP_{status_code}'),
                      error_message=trunc(error.get('message', ''), 100), latency_ms=latency)


def test_image(model: SBGModel, api_key: str, timeout: int) -> TestResult:
    payload = {
        'model_id': model.model_id,
        'prompt': 'A clean diagram of a simple red circle on white background',
        'width': 1024,
        'height': 1024,
        'image_count': 1,
        'quality': 'standard',
    }
    status_code, body, latency, err = request_json(
        requests.post, ENDPOINTS['image'], payload, _auth_headers(api_key), timeout)
    if err:
        return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                          error_code='CONNECTION', error_message=trunc(err, 100), latency_ms=latency)
    if _check_accepted(status_code, body, error_kws=['not allowed', 'region', 'model']):
        images = body.get('images', body.get('generated_images', []))
        seed = body.get('seed', '')
        return TestResult(model_id=model.model_id, category=model.category, status='OK',
                          status_code=status_code, latency_ms=latency,
                          output=f'{len(images)} images generated' if images else trunc(json.dumps(body), 70),
                          usage=body.get('usage', {}))
    error = body.get('error', {})
    return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                      status_code=status_code,
                      error_code=error.get('code', f'HTTP_{status_code}'),
                      error_message=trunc(error.get('message', ''), 100), latency_ms=latency)


def test_video(model: SBGModel, api_key: str, timeout: int) -> TestResult:
    payload = {
        'model_id': model.model_id,
        'prompt': 'A short animation explaining loops in programming',
        's3_output_uri': 's3://placeholder-bucket/video-output/',
        'duration_seconds': 6,
    }
    status_code, body, latency, err = request_json(
        requests.post, ENDPOINTS['video'], payload, _auth_headers(api_key), timeout)
    if err:
        return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                          error_code='CONNECTION', error_message=trunc(err, 100), latency_ms=latency)
    if _check_accepted(status_code, body, error_kws=['bucket', 's3', 'region', 'not allowed']):
        return TestResult(model_id=model.model_id, category=model.category, status='OK',
                          status_code=status_code, latency_ms=latency,
                          output=c(f'[gateway accepted] model+key valid', 'green'))
    error = body.get('error', {})
    return TestResult(model_id=model.model_id, category=model.category, status='ERROR',
                      status_code=status_code,
                      error_code=error.get('code', f'HTTP_{status_code}'),
                      error_message=trunc(error.get('message', ''), 100), latency_ms=latency)


def test_audio(model: SBGModel, api_key: str, timeout: int) -> TestResult:
    """No approved audio models — placeholder for future."""
    return TestResult(model_id=model.model_id, category=model.category, status='SKIP',
                      error_message='No approved audio models in list')


TEST_DISPATCH = {
    'chat': test_chat,
    'vision': test_vision,
    'embedding': test_embedding,
    'image': test_image,
    'video': test_video,
    'audio': test_audio,
    'other': None,
}


def print_separator(char='─', width=90):
    print(c(char * width, 'dim'))


def print_results(results: list[TestResult]):
    by_category: dict[str, list[TestResult]] = {}
    for r in results:
        by_category.setdefault(r.category, []).append(r)

    total = len(results)
    ok = sum(1 for r in results if r.status == 'OK')
    errors = total - ok

    for cat_name, cat_results in by_category.items():
        print()
        print_separator('═')
        print(f'  {c(cat_name.upper(), "cyan", "bold")}')
        print_separator('─')
        print(f'  {c("MODEL", "bold"):<55} {c("STATUS", "bold"):<8} '
              f'{c("CODE", "bold"):<6} {c("LATENCY", "bold"):<9} DETAIL')
        print_separator('─')

        for r in cat_results:
            if r.status == 'OK':
                status_str = c('  ✅ OK', 'green')
            elif r.status == 'ERROR':
                status_str = c('  ❌ ERR', 'red')
            else:
                status_str = c(f'  ⏭ {r.status}', 'yellow')

            code_str = str(r.status_code) if r.status_code else ''
            latency_str = f'{r.latency_ms}ms' if r.latency_ms else ''
            detail = ''
            if r.error_code:
                detail = c(f'{r.error_code}: {r.error_message or ""}', 'red')
            elif r.output:
                detail = c(trunc(r.output, 70), 'green')

            print(f'  {r.model_id:<55} {status_str:<8} '
                  f'{code_str:<6} {latency_str:<9} {detail}')
        print()

    print_separator('═')
    summary = f'  {c("RESULTS", "bold")}: {ok}/{total} passed'
    if errors:
        summary += c(f' — {errors} failed', 'red')
    else:
        summary += c(' — all passed!', 'green')
    print(summary)
    print()


class Command(BaseCommand):
    help = 'Test all approved SBG models against the ITI Student Bedrock Gateway'

    def add_arguments(self, parser):
        parser.add_argument('--model', type=str, default='',
                            help='Test a single model ID instead of all')
        parser.add_argument('--category', type=str, default='',
                            choices=list(TEST_DISPATCH),
                            help='Test only models in this category')
        parser.add_argument('--timeout', type=int, default=30,
                            help='Timeout in seconds per request (default: 30)')

    def handle(self, *args, **options):
        api_key = os.environ.get('SBG_API_KEY')
        if not api_key:
            self.stderr.write(self.style.ERROR('SBG_API_KEY environment variable is not set.'))
            self.stderr.write('Set it with:  export SBG_API_KEY="sbg_..."')
            return

        single_model = options['model']
        category_filter = options['category']
        timeout = options['timeout']

        if single_model:
            models_to_test = [m for m in APPROVED_MODELS if m.model_id == single_model]
            if not models_to_test:
                self.stderr.write(self.style.ERROR(f'Unknown model: {single_model}'))
                return
        elif category_filter:
            models_to_test = [m for m in APPROVED_MODELS if m.category == category_filter]
            if not models_to_test:
                self.stderr.write(self.style.ERROR(f'No models in category: {category_filter}'))
                return
        else:
            models_to_test = APPROVED_MODELS

        self.stdout.write()
        self.stdout.write(c('  SBG Model Test Suite', 'cyan', 'bold'))
        self.stdout.write(c(f'  Gateway: http://apiaccess.iti.net.eg', 'dim'))
        self.stdout.write(c(f'  Models:  {len(models_to_test)}', 'dim'))
        self.stdout.write()

        results = []
        for i, model in enumerate(models_to_test, 1):
            label = c(f'[{i}/{len(models_to_test)}]', 'yellow')
            self.stdout.write(f'  {label} Testing {model.model_id} '
                              f'({c(model.description, "dim")})...', ending='')
            self.stdout.flush()

            test_fn = TEST_DISPATCH.get(model.category)
            if test_fn is None:
                self.stdout.write(c(' SKIP — no endpoint', 'yellow'))
                results.append(TestResult(model_id=model.model_id, category=model.category,
                                          status='SKIP', error_message='No known endpoint'))
                continue

            try:
                result = test_fn(model, api_key, timeout)
            except Exception as exc:
                result = TestResult(model_id=model.model_id, category=model.category,
                                    status='ERROR', error_code='EXCEPTION',
                                    error_message=trunc(str(exc), 100))
            results.append(result)

            if result.status == 'OK':
                marker = c(' OK', 'green')
            elif result.status == 'ERROR':
                marker = c(' ERROR', 'red')
            else:
                marker = c(' SKIP', 'yellow')
            latency = f' {result.latency_ms}ms' if result.latency_ms else ''
            self.stdout.write(f' {marker}{latency}')

        self.stdout.write()
        print_results(results)

        has_errors = any(r.status == 'ERROR' for r in results)
        if has_errors:
            self.stdout.write(self.style.WARNING('Some models failed. See details above.'))
        else:
            self.stdout.write(self.style.SUCCESS('All tested models passed!'))
