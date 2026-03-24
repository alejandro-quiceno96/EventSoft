import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from app_areas.models import Areas

User = get_user_model()

class CrearAreaTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123'
        )
        
        # URL para los tests
        self.url = reverse('super_admin:crear_area')  # Ajustar según tu URL name
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
        
        # Datos válidos para crear área
        self.datos_validos = {
            'are_nombre': 'Tecnología',
            'are_descripcion': 'Área relacionada con tecnología e innovación'
        }
    
    def test_crear_area_exitosa(self):
        """CA1: Creación exitosa de un área con datos válidos"""
        # Verificar que no existe el área antes de crearla
        self.assertFalse(Areas.objects.filter(are_nombre='Tecnología').exists())
        
        # Realizar solicitud POST para crear área
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('super_admin:index_super_admin'))
        
        # Verificar que el área fue creada en la base de datos
        self.assertTrue(Areas.objects.filter(are_nombre='Tecnología').exists())
        
        area_creada = Areas.objects.get(are_nombre='Tecnología')
        self.assertEqual(area_creada.are_descripcion, 'Área relacionada con tecnología e innovación')
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Área creada exitosamente.")
    
    def test_crear_area_solo_nombre(self):
        """CA1: Creación de área con solo nombre (descripción opcional)"""
        datos_solo_nombre = {
            'are_nombre': 'Ciencias Básicas',
            'are_descripcion': ''  # Descripción vacía
        }
        
        response = self.client.post(self.url, datos_solo_nombre)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Areas.objects.filter(are_nombre='Ciencias Básicas').exists())
        
        area_creada = Areas.objects.get(are_nombre='Ciencias Básicas')
        self.assertEqual(area_creada.are_descripcion, '')
    
    def test_crear_area_nombre_largo(self):
        """CA1: Creación de área con nombre en límite de caracteres"""
        nombre_largo = 'A' * 100  # Máximo permitido por el modelo
        datos_nombre_largo = {
            'are_nombre': nombre_largo,
            'are_descripcion': 'Descripción de área con nombre largo'
        }
        
        response = self.client.post(self.url, datos_nombre_largo)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Areas.objects.filter(are_nombre=nombre_largo).exists())
    
    def test_crear_area_descripcion_larga(self):
        """CA1: Creación de área con descripción en límite de caracteres"""
        descripcion_larga = 'D' * 400  # Máximo permitido por el modelo
        datos_descripcion_larga = {
            'are_nombre': 'Área con Descripción Larga',
            'are_descripcion': descripcion_larga
        }
        
        response = self.client.post(self.url, datos_descripcion_larga)
        
        self.assertEqual(response.status_code, 302)
        area_creada = Areas.objects.get(are_nombre='Área con Descripción Larga')
        self.assertEqual(area_creada.are_descripcion, descripcion_larga)
    
    def test_crear_areas_multiples(self):
        """CA1: Creación secuencial de múltiples áreas"""
        areas_a_crear = [
            {'nombre': 'Matemáticas', 'descripcion': 'Área de matemáticas puras y aplicadas'},
            {'nombre': 'Literatura', 'descripcion': 'Área de estudios literarios'},
            {'nombre': 'Arte', 'descripcion': 'Área de expresión artística'}
        ]
        
        for area_data in areas_a_crear:
            with self.subTest(area=area_data['nombre']):
                datos = {
                    'are_nombre': area_data['nombre'],
                    'are_descripcion': area_data['descripcion']
                }
                
                response = self.client.post(self.url, datos)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(Areas.objects.filter(are_nombre=area_data['nombre']).exists())
        
        # Verificar que se crearon todas las áreas
        self.assertEqual(Areas.objects.count(), 3)
    
    def test_metodo_get_redirige(self):
        """CA2: Método GET redirige sin crear área"""
        # Contar áreas existentes antes
        areas_iniciales = Areas.objects.count()
        
        # Intentar crear área con GET (no debería funcionar)
        response = self.client.get(self.url, self.datos_validos)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('super_admin:index_super_admin'))
        
        # Verificar que NO se creó el área
        self.assertEqual(Areas.objects.count(), areas_iniciales)
        self.assertFalse(Areas.objects.filter(are_nombre='Tecnología').exists())
    
    def test_metodo_put_redirige(self):
        """CA2: Método PUT redirige sin crear área"""
        areas_iniciales = Areas.objects.count()
        
        # Intentar crear área con PUT
        response = self.client.put(self.url, data=self.datos_validos)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Areas.objects.count(), areas_iniciales)
    
    def test_metodo_delete_redirige(self):
        """CA2: Método DELETE redirige sin crear área"""
        areas_iniciales = Areas.objects.count()
        
        # Intentar crear área con DELETE
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Areas.objects.count(), areas_iniciales)
    
    def test_crear_area_duplicada(self):
        """CA1: Intentar crear área con nombre duplicado"""
        # Crear primera área
        response1 = self.client.post(self.url, self.datos_validos)
        self.assertEqual(response1.status_code, 302)
        self.assertTrue(Areas.objects.filter(are_nombre='Tecnología').exists())
        
        # Intentar crear área con mismo nombre
        areas_antes_segundo_intento = Areas.objects.count()
        response2 = self.client.post(self.url, self.datos_validos)
        
        # La función actual no valida duplicados, así que intentará crear otra
        self.assertEqual(response2.status_code, 302)
        
        # Depende si el modelo tiene unique=True en are_nombre
        # Si no tiene, se creará duplicado; si tiene, fallará silenciosamente
        # Por ahora solo verificamos que redirige
    
    def test_mensaje_exito_presente(self):
        """CA3: Verificar que el mensaje de éxito se muestra correctamente"""
        response = self.client.post(self.url, self.datos_validos)
        
        # Seguir la redirección para verificar el mensaje en el contexto
        response_final = self.client.get(response.url)
        
        # Verificar que la página carga correctamente después de la redirección
        self.assertEqual(response_final.status_code, 200)
        
        # Los mensajes se almacenan en la sesión, podemos verificarlos así:
        messages = [msg for msg in get_messages(response.wsgi_request)]
        self.assertTrue(any("Área creada exitosamente." in str(msg) for msg in messages))
    
    def test_estructura_datos_area(self):
        """CA1: Verificar que los datos del área se guardan correctamente"""
        datos_especificos = {
            'are_nombre': 'Inteligencia Artificial',
            'are_descripcion': 'Área enfocada en ML, Deep Learning y AI'
        }
        
        response = self.client.post(self.url, datos_especificos)
        
        # Verificar que el área se creó con los datos correctos
        area_creada = Areas.objects.get(are_nombre='Inteligencia Artificial')
        self.assertEqual(area_creada.are_nombre, 'Inteligencia Artificial')
        self.assertEqual(area_creada.are_descripcion, 'Área enfocada en ML, Deep Learning y AI')
        
        # Verificar el método __str__
        self.assertEqual(str(area_creada), 'Inteligencia Artificial')
    
    def test_redireccion_correcta(self):
        """CA3: Verificar que siempre redirige a index_super_admin"""
        # Con POST exitoso
        response_post = self.client.post(self.url, self.datos_validos)
        self.assertEqual(response_post.url, reverse('super_admin:index_super_admin'))
        
        # Con GET
        response_get = self.client.get(self.url)
        self.assertEqual(response_get.url, reverse('super_admin:index_super_admin'))
        
        # Con PUT
        response_put = self.client.put(self.url)
        self.assertEqual(response_put.url, reverse('super_admin:index_super_admin'))
    
    def test_campos_opcionales_y_requeridos(self):
        """CA1: Probar diferentes combinaciones de campos"""
        casos_prueba = [
            {
                'datos': {'are_nombre': 'Solo Nombre', 'are_descripcion': ''},
                'descripcion': 'Solo nombre, descripción vacía'
            },
            {
                'datos': {'are_nombre': 'Nombre Normal', 'are_descripcion': 'Descripción normal'},
                'descripcion': 'Ambos campos completos'
            },
            {
                'datos': {'are_nombre': '   Nombre con espacios   ', 'are_descripcion': '   Descripción con espacios   '},
                'descripcion': 'Campos con espacios'
            }
        ]
        
        for caso in casos_prueba:
            with self.subTest(descripcion=caso['descripcion']):
                areas_iniciales = Areas.objects.count()
                
                response = self.client.post(self.url, caso['datos'])
                self.assertEqual(response.status_code, 302)
                
                # Verificar que se creó el área (si el nombre no está vacío)
                if caso['datos']['are_nombre'].strip():
                    self.assertEqual(Areas.objects.count(), areas_iniciales + 1)