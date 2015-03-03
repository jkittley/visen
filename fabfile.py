#encoding:UTF-8
from os import getcwd, sep, remove
from fabric.api import cd, lcd
from fabric.operations import run, local, prompt, put, sudo
from fabric.network import needs_host
from fabric.state import env, output
from fabric.contrib import files

env.project_local = 'visen'
env.project_remote = 'visen'

# the db name must be at most 16 chars
env.dbname = env.project_remote
env.dbpass = 'your_password'

env.hosts = ['hci.ecs.soton.ac.uk'] # list of hosts for deployment here
#env.hostpath = '/srv/django-projects/'+env.project_remote+'/'

env.activate = 'source /srv/pve/' + env.project_remote + '/bin/activate'

env.context = {'remote_name': env.project_remote, 'dbname': env.dbname, 'dbpass': env.dbpass}

def virtualenv(command):
    run(env.activate + ' && ' + command)

def set_user():
    #run('uname -s')
    env.user = prompt("Please specify username for server: ")

def touch():
    with cd('/srv/django-projects/' + env.project_remote + '/' + env.project_remote + '/'):
        run('touch wsgi.py')

def sync():
    my_rsync_project(remote_dir="/srv/django-projects/" + env.project_remote + "/",
                   #local_dir=env.project_local + "/",
                   local_dir='./',
                   exclude=("fabfile.py","*.pyc",".svn","*.dat", "venv",
                            "uploads", 'media'),
                   delete=False
                  )

def collect_static():
    with cd('/srv/django-projects/' + env.project_remote + '/'):
        virtualenv('python manage.py collectstatic --noinput')

def deploy():
    set_user()
    sync()
    collect_static()
    touch()


def reset_db():
    set_user()
    with cd('/srv/django-projects/' + env.project_remote + '/'):
        virtualenv('python manage.py syncdb')


def pull_data():
    set_user()
    with cd('/srv/django-projects/' + env.project_remote + '/'):
        virtualenv('python manage.py pull_protected_store_data')

#####

def setup_virtualenv():
    set_user()
    with lcd("../" + env.project_local + "/"):
        put("requirements.txt", "/tmp/")

    with cd('/srv/pve/'):
        run('virtualenv --no-site-packages %(remote_name)s' % env.context)

    virtualenv('pip install -r /tmp/requirements.txt')

def setup_db():
    set_user()
    command = """echo "create database if not exists %(dbname)s; GRANT ALL ON %(dbname)s.* TO '%(dbname)s'@'localhost' IDENTIFIED BY '%(dbname)s@%(dbpass)s'; " | mysql -u root -p%(dbpass)s""" % env.context
    run(command)

def setup_project():
    set_user()
    with cd('/srv/django-projects/'):
        virtualenv('django-admin.py startproject %(remote_name)s' % env.context)

def setup_logfile():
    set_user()
    sudo('mkdir -p /srv/log/')
    with cd('/srv/log/'):
        sudo('mkdir -p ' + env.project_remote)
        sudo("echo 'start' > " + env.project_remote + '/usage.log')
        # for older ubuntu (or updates from its existing installation) use:
        #sudo('chown www-data:admin ' + env.project_remote + '/usage.log')
        # for ubuntu 12.04 use:
        sudo('chown www-data:sudo ' + env.project_remote + '/usage.log')
        sudo('chmod g+rw ' + env.project_remote + '/usage.log')

def setup_directories():
    set_user()
    with cd('/srv/django-projects/' + env.project_remote + '/'):
        run('mkdir templates')
        run('mkdir media')

def setup_servers():
    nginxConf_http = """
    # this is to allow networked sensors to post data via HTTP (not HTTPS)
    location /%s/rawinput {
        #rewrite (.*) https://%s/$1 permanent;
        proxy_pass http://localhost:8080;
        include /etc/nginx/proxy.conf;
    }

    location /%s {
        rewrite (.*) https://%s/$1 permanent;
    }
    """ % (env.project_remote, env.hosts[0], env.project_remote, env.hosts[0])

    nginxConf_https = """
    location /%(remote_name)s/media/ {
        alias /srv/django-projects/%(remote_name)s/%(remote_name)s/media/;
    }

    location /%(remote_name)s/admin-media/ {
        alias /srv/pve/%(remote_name)s/lib/python2.7/site-packages/django/contrib/admin/media/;
    }

    location /%(remote_name)s/ {
        proxy_pass http://localhost:8080;
        include /etc/nginx/proxy.conf;
    }""" % env.context


    set_user()
    open('tmp.txt', 'w').write(nginxConf_http)
    files.upload_template('tmp.txt', '/etc/nginx/django-projects/' + env.project_remote + '.http', use_sudo=True, backup=False)
    remove('tmp.txt')

    open('tmp.txt', 'w').write(nginxConf_https)
    files.upload_template('tmp.txt', '/etc/nginx/django-projects/' + env.project_remote + '.https', use_sudo=True, backup=False)
    remove('tmp.txt')

    apacheConf = """
<Directory /srv/django-projects/%(remote_name)s/%(remote_name)s/>
    <Files wsgi.py>
        Order deny,allow
        Allow from all
    </Files>
</Directory>

WSGIScriptAlias /%(remote_name)s /srv/django-projects/%(remote_name)s/%(remote_name)s/wsgi.py
WSGIDaemonProcess %(remote_name)s python-path=/srv/django-projects/%(remote_name)s/:/srv/pve/%(remote_name)s/lib/python2.7/site-packages user=www-data group=www-data threads=25
<Location /%(remote_name)s>
    WSGIProcessGroup %(remote_name)s
</Location>
    """ % env.context

    open('tmp.txt', 'w').write(apacheConf)
    files.upload_template('tmp.txt', '/etc/apache2/django-projects/' + env.project_remote, use_sudo=True, backup=False)
    remove('tmp.txt')

    # restart nginx and reload apache
    sudo('/etc/init.d/nginx restart')
    sudo('/etc/init.d/apache2 reload')


def setup():
    setup_virtualenv()
    setup_db()
    setup_project()
    setup_directories()
    setup_servers()
    setup_logfile()

@needs_host
def my_rsync_project(remote_dir, local_dir=None, exclude=(), delete=False,
    extra_opts=''):
    """
    Synchronize a remote directory with the current project directory via rsync.

    Where ``upload_project()`` makes use of ``scp`` to copy one's entire
    project every time it is invoked, ``rsync_project()`` uses the ``rsync``
    command-line utility, which only transfers files newer than those on the
    remote end.

    ``rsync_project()`` is thus a simple wrapper around ``rsync``; for
    details on how ``rsync`` works, please see its manpage. ``rsync`` must be
    installed on both your local and remote systems in order for this operation
    to work correctly.

    This function makes use of Fabric's ``local()`` operation, and returns the
    output of that function call; thus it will return the stdout, if any, of
    the resultant ``rsync`` call.

    ``rsync_project()`` takes the following parameters:

    * ``remote_dir``: the only required parameter, this is the path to the
      **parent** directory on the remote server; the project directory will be
      created inside this directory. For example, if one's project directory is
      named ``myproject`` and one invokes ``rsync_project('/home/username/')``,
      the resulting project directory will be ``/home/username/myproject/``.
    * ``local_dir``: by default, ``rsync_project`` uses your current working
      directory as the source directory; you may override this with
      ``local_dir``, which should be a directory path.
    * ``exclude``: optional, may be a single string, or an iterable of strings,
      and is used to pass one or more ``--exclude`` options to ``rsync``.
    * ``delete``: a boolean controlling whether ``rsync``'s ``--delete`` option
      is used. If True, instructs ``rsync`` to remove remote files that no
      longer exist locally. Defaults to False.
    * ``extra_opts``: an optional, arbitrary string which you may use to pass
      custom arguments or options to ``rsync``.

    Furthermore, this function transparently honors Fabric's port and SSH key
    settings. Calling this function when the current host string contains a
    nonstandard port, or when ``env.key_filename`` is non-empty, will use the
    specified port and/or SSH key filename(s).

    For reference, the approximate ``rsync`` command-line call that is
    constructed by this function is the following:

        rsync [--delete] [--exclude exclude[0][, --exclude[1][, ...]]] \\
            -pthrvz [extra_opts] <local_dir> <host_string>:<remote_dir>

    """
    # Turn single-string exclude into a one-item list for consistency
    if not hasattr(exclude, '__iter__'):
        exclude = (exclude,)
    # Create --exclude options from exclude list
    exclude_opts = ' --exclude "%s"' * len(exclude)
    # Double-backslash-escape
    exclusions = tuple([str(s).replace('"', '\\\\"') for s in exclude])
    # Honor SSH key(s)
    key_string = ""
    if env.key_filename:
        keys = env.key_filename
        # For ease of use, coerce stringish key filename into list
        if not isinstance(env.key_filename, (list, tuple)):
            keys = [keys]
        key_string = "-i " + " -i ".join(keys)
    # Honor nonstandard port
    port_string = ("-p %s" % env.port) if (env.port != '22') else ""
    # RSH
    rsh_string = ""
    if key_string or port_string:
        rsh_string = "--rsh='ssh %s %s'" % (port_string, key_string)
    # Set up options part of string
    options_map = {
        'delete': '--delete' if delete else '',
        'exclude': exclude_opts % exclusions,
        'rsh': rsh_string,
        'extra': extra_opts
    }
    options = "%(delete)s%(exclude)s -rv %(extra)s %(rsh)s" % options_map
    # Get local directory
    if local_dir is None:
        local_dir = '../' + getcwd().split(sep)[-1]
    # Create and run final command string
    cmd = "rsync %s %s %s@%s:%s" % (options, local_dir, env.user,
        env.host, remote_dir)
    if output.running:
        print("[%s] rsync_project: %s" % (env.host_string, cmd))
    return local(cmd)


