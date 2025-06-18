from django.contrib import admin
from .models import Usuario
from django.contrib.auth.admin import UserAdmin

class UsuarioAdmin(UserAdmin):
    model = Usuario
    fieldsets = UserAdmin.fieldsets + (
        (None, {
            'fields': ('tipo_documento', 'documento_identidad','segundo_nombre', 'segundo_apellido', 'fecha_nacimiento', 'telefono'),
        }),
    )
    
    list_display = UserAdmin.list_display + ('tipo_documento', 'documento_identidad', 'fecha_nacimiento')

admin.site.register(Usuario, UsuarioAdmin)