from django.apps import AppConfig
import sys
import os


class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'

    def ready(self):
        """Create admin user automatically on server startup"""
        # Skip during migrations, collectstatic, and other management commands
        if len(sys.argv) > 1 and sys.argv[1] in ['migrate', 'makemigrations', 'collectstatic', 'test', 'shell', 'dbshell']:
            return
        
        # For runserver: only run in the main process (not in reloader subprocess)
        # For WSGI: always run (RUN_MAIN won't be set)
        if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
            return
        
        try:
            from django.contrib.auth import get_user_model
            from django.db import transaction
            from django.db import connection
            
            # Check if database is ready
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            User = get_user_model()
            
            # Admin credentials
            admin_username = 'mainadmin12mi'
            admin_password = 'Asdfjkj2324.,23idf'
            admin_email = 'admin@cloudcontract.local'
            
            # Check if user already exists
            if not User.objects.filter(username=admin_username).exists():
                with transaction.atomic():
                    # Create superuser
                    admin_user = User.objects.create_user(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password
                    )
                    admin_user.is_staff = True
                    admin_user.is_superuser = True
                    admin_user.save()
                    print(f"✓ Admin user '{admin_username}' created successfully")
            else:
                # Update password and permissions if user exists (in case they changed)
                admin_user = User.objects.get(username=admin_username)
                needs_update = False
                
                if not admin_user.check_password(admin_password):
                    admin_user.set_password(admin_password)
                    needs_update = True
                
                if not admin_user.is_staff:
                    admin_user.is_staff = True
                    needs_update = True
                
                if not admin_user.is_superuser:
                    admin_user.is_superuser = True
                    needs_update = True
                
                if needs_update:
                    admin_user.save()
                    print(f"✓ Admin user '{admin_username}' updated successfully")
        except Exception as e:
            # Silently fail if database is not ready (e.g., during initial migrations)
            error_str = str(e).lower()
            if 'no such table' not in error_str and 'relation' not in error_str and 'does not exist' not in error_str:
                # Only print if it's not a database-not-ready error
                pass
