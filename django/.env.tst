DEBUG=True
PROJECT_SHORT_NAME='TIIP'
PROJECT_NAME='UNICEF T4D & Innovation Inventory Portal'
SITE_URL=invent-tst.unitst.org
DEFAULT_FROM_EMAIL='UNICEF T4D & Innovation Inventory Portal <noreply@invent.unicef.org>'
REDIS_URL=redis
AZURE_CALLBACK_URL=https://invent-tst.unitst.org/accounts/azure/login/callback/
SENTRY_DSN=
EMAIL_SENDING_PRODUCTION=True
EMAIL_HOST=mailhog.invent-dev.svc.cluster.local
EMAIL_PORT=1025
ALLOWED_HOSTS='*'
CSRF_TRUSTED_ORIGINS='*'
MIGRATE_PHASES=False
SIMPLE_FEEDBACK_SEND_TO='invent@unicef.org'
API_MAINTAINER=invent@unicef.org
EMAIL_VALIDATOR_REGEX='(unicef.org|pulilab.com)$'
ENABLE_API_REGISTRATION=True
DEPLOY_VERSION="4.0.0"
POSTGRES_USER=tstinventusr
DATABASE_HOST=pgsql-14-reserved-invent-db-devstg.postgres.database.azure.com
DATABASE_NAME=inventdb_tst