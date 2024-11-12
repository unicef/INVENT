load('ext://helm_resource', 'helm_resource', 'helm_repo')
load('ext://uibutton', 'cmd_button', 'bool_input', 'text_input', 'location')

# Add PostgreSQL Helm resource (https://artifacthub.io/packages/helm/bitnami/postgresql)
helm_repo('bitnami', 'https://charts.bitnami.com/bitnami',labels=['helm-charts'])
helm_repo('codecentric', 'https://codecentric.github.io/helm-charts',labels=['helm-charts'])
helm_resource(
    resource_deps=['bitnami'],
    name='postgres',
    chart='bitnami/postgresql',
    namespace='default',
    flags=[
        '--set=image.tag=15.2.0',
        '--set=auth.enablePostgresUser=true',
        '--set=auth.postgresPassword=postgres'
    ],
    port_forwards=['30011:5432'],
    labels=['database']
)

if os.path.exists('/tmp'):
    os_command = ['sh', '-c']
    pod_exec_script = 'kubectl exec deployment/$deployment -- $command'
    translations_pod_exec_script = 'kubectl exec deployment/$deployment -c $container -- $command'
    translations_script_cmd = './extract_translations.sh'
else:
    os_command = ['cmd', '/c']
    pod_exec_script = 'kubectl exec deployment/%deployment% -- %command%'
    translations_pod_exec_script = 'kubectl exec deployment/%deployment% -c %container% -- %command%'
    translations_script_cmd = 'bash ./extract_translations.sh'

local_resource(
    name='copy-dump',
    resource_deps=['postgres'],
    cmd="""kubectl cp dump_anon.sql postgres-postgresql-0:/tmp/dump_anon.sql
    """,
    allow_parallel=True,
    labels=['database']
)

local_resource(
    name='import-dump',
    resource_deps=['copy-dump'],
    cmd='kubectl exec postgres-postgresql-0 -- env PGPASSWORD=postgres psql -U postgres -d postgres -f /tmp/dump_anon.sql',
    allow_parallel=True,
    labels=['database']
)

local_resource(
    name='reset-sequences',
    resource_deps=['import-dump'],
    cmd="""kubectl exec postgres-postgresql-0 -- env PGPASSWORD=postgres psql -U postgres -d postgres -c "DO \\$\\$ DECLARE seq RECORD; BEGIN FOR seq IN SELECT pg_get_serial_sequence(c.oid::regclass::text, a.attname) AS sequence_name, c.oid::regclass::text AS tablename, a.attname AS colname FROM pg_class c JOIN pg_attribute a ON c.oid = a.attrelid WHERE c.relkind = 'r' AND a.attnum > 0 AND pg_get_serial_sequence(c.oid::regclass::text, a.attname) IS NOT NULL LOOP EXECUTE format('SELECT setval(''%s'', COALESCE((SELECT MAX(%I) FROM %s) + 1, 1), false)', seq.sequence_name, seq.colname, seq.tablename); END LOOP; END; \\$\\$;" """,
    allow_parallel=True,
    labels=['database']
)

helm_resource(
    resource_deps=['bitnami'],
    name='redis',
    chart='bitnami/redis',
    namespace='default',
    flags=[
        '--set=image.tag=4.0.10',
        '--set=master.count=1',
        '--set=replica.replicaCount=0',
        '--set=auth.enabled=false',
        '--set=auth.sentinel=false',
        '--set=cluster.enabled=false',
        '--set=sysctl.enabled=true',
        '--set=sysctl.mountHostSys=true',
        '--set=sysctl.command[0]=/bin/sh',
        '--set=sysctl.command[1]=-c',
        '--set=sysctl.command[2]=install_packages procps; sysctl -w net.core.somaxconn=1000; echo never > /host-sys/kernel/mm/transparent_hugepage/enabled',
        '--set=master.readinessProbe.exec.command[0]=sh',
        '--set=master.readinessProbe.exec.command[1]=-c',
        '--set=master.readinessProbe.exec.command[2]=/health/ping_readiness_local.sh 5',
        '--set=master.readinessProbe.initialDelaySeconds=30',
        '--set=master.readinessProbe.periodSeconds=10',
        '--set=master.readinessProbe.timeoutSeconds=5',
        '--set=master.readinessProbe.failureThreshold=3',
        '--set=master.readinessProbe.successThreshold=1'
    ],
    labels=['redis']
)

helm_resource(
    resource_deps=['codecentric'],
    name='mailhog',
    chart='codecentric/mailhog',
    namespace='default',
    flags=[
        '--set=auth.enabled=false',
    ],
    port_forwards=['30012:8025'],
    labels=['mailhog']
)

docker_build(
    'invent-django',
    './',
    dockerfile='Dockerfile.django',
    live_update=[
        sync('django/', '/src'),
        run('cd /src && pip install -r requirements.txt',
            trigger=['./django/requirements.txt']),
        run('cd /src && python manage.py migrate',
            trigger=['./django/*/migrations']),
    ],
)

helm_resource(
    resource_deps=['postgres'],
    name='invent-django',
    chart='./django/helm',
    deps=['./django/helm'],
    image_deps=['invent-django'],
    namespace='default',
    image_keys=[('image.repository', 'image.tag')],
    flags=[
        '-f=./django/helm/values-dev.yaml',
    ],
    labels=['backend']
)


# Buttons to execute scripts inside pods through the Tilt UI
# Execute Unit Tests
cmd_button('exec_unit_tests',
    argv=os_command + [pod_exec_script],
    resource='invent-django',
    env=[
        'deployment=invent-django',
        'command=/bin/bash run_unit_tests.sh 100',
    ],
    icon_name='bug_report',
    text='Execute Unit tests',
)

# Create the Super User in Django
cmd_button('exec_create_super_user',
    argv=os_command + [pod_exec_script],
    resource='invent-django',
    env=[
        'deployment=invent-django',
        'command=python manage.py create_superuser',
    ],
    icon_name='person_add',
    text='Create superuser',
)

# Run the django migrations
cmd_button('exec_migrate',
    argv=os_command + [pod_exec_script],
    resource='invent-django',
    env=[
        'deployment=invent-django',
        'command=python manage.py migrate --noinput',
    ],
    icon_name='arrow_forward_ios',
    text='Run migrations',
)

# # Run the translation extraction
cmd_button('extract_translations',
    argv=os_command + [translations_pod_exec_script],
    resource='invent-frontend',
    env=[
        'deployment=invent-frontend',
        'container=invent-frontend',
        'command=yarn translation:extract'
    ],
    icon_name='translate',
    text='Extract translations',
)

############# FE Tilt Configuration ##################

docker_build(
    'localhost:5001/invent_nginx',
    './',
    dockerfile='Dockerfile.nginx',
)

docker_build(
    'localhost:5001/invent_frontend',
    './',
    dockerfile='Dockerfile.frontend',
)

yaml = helm(
    './frontend/helm',
    # The release name, equivalent to helm --name
    name='invent-frontend',
    # The namespace to install in, equivalent to helm --namespace
    namespace='default',
    # The values file to substitute into the chart.
    values=['./frontend/helm/values-dev.yaml'],
    # Values to set from the command-line
    set=['ingress.enabled=false']
)
k8s_yaml(yaml)

k8s_resource(
    'invent-frontend',
    port_forwards='8888:80',
    objects = ['invent-frontend:ServiceAccount'],
    pod_readiness='wait',
    labels='frontend'
)

k8s_kind('local')
