from .development import *  

DEBUG = True

REST_FRAMEWORK = REST_FRAMEWORK.copy()
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
    'anon': '10000/min',
    'user': '10000/min',
    'login': '10000/min',
    'ai': '10000/min',
}
