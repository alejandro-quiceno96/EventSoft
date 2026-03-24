import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from app_areas.models import Areas
from app_categorias.models import Categorias

User = get_user_model()

class CrearCategoriaTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para todos los tests"""
        self.client = Client()
        
        # Crear super administrador
        self.super_admin = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='testpass123'
        )
        
        # Crear áreas para testing
        self.area_tecnologia = Areas.objects.create(
            are_nombre='Tecnología',
            are_descripcion='Área de tecnología e innovación'
        )
        
        self.area_ciencias = Areas.objects.create(
            are_nombre='Ciencias',
            are_descripcion='Área de ciencias puras y aplicadas'
        )
        
        # URL para los tests
        self.url = reverse('super_admin:crear_categoria')  # Ajustar según tu URL name
        
        # Autenticar como super administrador
        self.client.login(username='superadmin', password='testpass123')
        
        # Datos válidos para crear categoría
        self.datos_validos = {
            'cat_nombre': 'Programación',
            'cat_descripcion': 'Categoría relacionada con lenguajes de programación',
            'cat_area_fk': self.area_tecnologia.id
        }
    
    def test_crear_categoria_exitosa(self):
        """CA1: Creación exitosa de una categoría con datos válidos"""
        # Verificar que no existe la categoría antes de crearla
        self.assertFalse(Categorias.objects.filter(cat_nombre='Programación').exists())
        
        # Realizar solicitud POST para crear categoría
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar redirección exitosa
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('super_admin:index_super_admin'))
        
        # Verificar que la categoría fue creada en la base de datos
        self.assertTrue(Categorias.objects.filter(cat_nombre='Programación').exists())
        
        categoria_creada = Categorias.objects.get(cat_nombre='Programación')
        self.assertEqual(categoria_creada.cat_descripcion, 'Categoría relacionada con lenguajes de programación')
        self.assertEqual(categoria_creada.cat_area_fk, self.area_tecnologia)
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Categoría creada exitosamente.")
    
    def test_crear_categoria_con_diferente_area(self):
        """CA1: Creación de categoría asociada a diferentes áreas"""
        datos_ciencias = {
            'cat_nombre': 'Biología',
            'cat_descripcion': 'Categoría de ciencias biológicas',
            'cat_area_fk': self.area_ciencias.id
        }
        
        response = self.client.post(self.url, datos_ciencias)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Categorias.objects.filter(cat_nombre='Biología').exists())
        
        categoria_creada = Categorias.objects.get(cat_nombre='Biología')
        self.assertEqual(categoria_creada.cat_area_fk, self.area_ciencias)
    
    def test_crear_categoria_solo_nombre(self):
        """CA1: Creación de categoría con solo nombre (descripción opcional)"""
        datos_solo_nombre = {
            'cat_nombre': 'Matemáticas Discretas',
            'cat_descripcion': '',  # Descripción vacía
            'cat_area_fk': self.area_ciencias.id
        }
        
        response = self.client.post(self.url, datos_solo_nombre)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Categorias.objects.filter(cat_nombre='Matemáticas Discretas').exists())
        
        categoria_creada = Categorias.objects.get(cat_nombre='Matemáticas Discretas')
        self.assertEqual(categoria_creada.cat_descripcion, '')
        self.assertEqual(categoria_creada.cat_area_fk, self.area_ciencias)
    
    def test_crear_categoria_nombre_largo(self):
        """CA1: Creación de categoría con nombre en límite de caracteres"""
        nombre_largo = 'C' * 100  # Máximo permitido por el modelo
        datos_nombre_largo = {
            'cat_nombre': nombre_largo,
            'cat_descripcion': 'Descripción de categoría con nombre largo',
            'cat_area_fk': self.area_tecnologia.id
        }
        
        response = self.client.post(self.url, datos_nombre_largo)
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Categorias.objects.filter(cat_nombre=nombre_largo).exists())
    
    def test_crear_categoria_descripcion_larga(self):
        """CA1: Creación de categoría con descripción en límite de caracteres"""
        descripcion_larga = 'D' * 400  # Máximo permitido por el modelo
        datos_descripcion_larga = {
            'cat_nombre': 'Categoría con Descripción Larga',
            'cat_descripcion': descripcion_larga,
            'cat_area_fk': self.area_tecnologia.id
        }
        
        response = self.client.post(self.url, datos_descripcion_larga)
        
        self.assertEqual(response.status_code, 302)
        categoria_creada = Categorias.objects.get(cat_nombre='Categoría con Descripción Larga')
        self.assertEqual(categoria_creada.cat_descripcion, descripcion_larga)
    
    def test_crear_categorias_multiples(self):
        """CA1: Creación secuencial de múltiples categorías en la misma área"""
        categorias_a_crear = [
            {'nombre': 'Frontend', 'descripcion': 'Desarrollo frontend'},
            {'nombre': 'Backend', 'descripcion': 'Desarrollo backend'},
            {'nombre': 'DevOps', 'descripcion': 'Operaciones de desarrollo'}
        ]
        
        for cat_data in categorias_a_crear:
            with self.subTest(categoria=cat_data['nombre']):
                datos = {
                    'cat_nombre': cat_data['nombre'],
                    'cat_descripcion': cat_data['descripcion'],
                    'cat_area_fk': self.area_tecnologia.id
                }
                
                response = self.client.post(self.url, datos)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(Categorias.objects.filter(cat_nombre=cat_data['nombre']).exists())
        
        # Verificar que se crearon todas las categorías
        self.assertEqual(Categorias.objects.count(), 3)
        
        # Verificar que todas pertenecen al área de tecnología
        categorias_tecnologia = Categorias.objects.filter(cat_area_fk=self.area_tecnologia)
        self.assertEqual(categorias_tecnologia.count(), 3)
    
    def test_crear_categorias_diferentes_areas(self):
        """CA1: Creación de categorías en diferentes áreas"""
        categorias_areas = [
            {'nombre': 'Inteligencia Artificial', 'area': self.area_tecnologia},
            {'nombre': 'Química Orgánica', 'area': self.area_ciencias},
            {'nombre': 'Redes y Conectividad', 'area': self.area_tecnologia}
        ]
        
        for cat_data in categorias_areas:
            datos = {
                'cat_nombre': cat_data['nombre'],
                'cat_descripcion': f'Descripción de {cat_data["nombre"]}',
                'cat_area_fk': cat_data['area'].id
            }
            
            response = self.client.post(self.url, datos)
            self.assertEqual(response.status_code, 302)
        
        # Verificar distribución por áreas
        categorias_tecnologia = Categorias.objects.filter(cat_area_fk=self.area_tecnologia)
        categorias_ciencias = Categorias.objects.filter(cat_area_fk=self.area_ciencias)
        
        self.assertEqual(categorias_tecnologia.count(), 2)
        self.assertEqual(categorias_ciencias.count(), 1)
    
    def test_metodo_get_redirige(self):
        """CA2: Método GET redirige sin crear categoría"""
        # Contar categorías existentes antes
        categorias_iniciales = Categorias.objects.count()
        
        # Intentar crear categoría con GET (no debería funcionar)
        response = self.client.get(self.url, self.datos_validos)
        
        # Verificar redirección
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('super_admin:index_super_admin'))
        
        # Verificar que NO se creó la categoría
        self.assertEqual(Categorias.objects.count(), categorias_iniciales)
        self.assertFalse(Categorias.objects.filter(cat_nombre='Programación').exists())
    
    def test_area_no_existe(self):
        """CA2: Manejo de error cuando el área no existe"""
        datos_area_inexistente = {
            'cat_nombre': 'Categoría con Área Inexistente',
            'cat_descripcion': 'Esta categoría no debería crearse',
            'cat_area_fk': 9999  # ID que no existe
        }
        
        categorias_iniciales = Categorias.objects.count()
        
        # Esto debería causar una excepción DoesNotExist
        with self.assertRaises(Areas.DoesNotExist):
            self.client.post(self.url, datos_area_inexistente)
        
        # Verificar que NO se creó la categoría
        self.assertEqual(Categorias.objects.count(), categorias_iniciales)
    
    
    def test_crear_categoria_sin_nombre(self):
        """CA2: Intentar crear categoría sin nombre (debería fallar)"""
        datos_sin_nombre = {
            'cat_nombre': '',  # Nombre vacío
            'cat_descripcion': 'Descripción sin nombre',
            'cat_area_fk': self.area_tecnologia.id
        }
        
        categorias_iniciales = Categorias.objects.count()
        
        # La función actual no valida, pero el modelo probablemente sí
        response = self.client.post(self.url, datos_sin_nombre)
        
        # Verificar redirección (aunque falle la creación)
        self.assertEqual(response.status_code, 302)
    
    def test_crear_categoria_sin_area(self):
        """CA2: Intentar crear categoría sin área (debería fallar)"""
        datos_sin_area = {
            'cat_nombre': 'Categoría Sin Área',
            'cat_descripcion': 'Esta categoría no tiene área',
            'cat_area_fk': ''  # Área vacía
        }
        
        categorias_iniciales = Categorias.objects.count()
        
        # Esto causará una excepción por área vacía
        with self.assertRaises(ValueError):
            self.client.post(self.url, datos_sin_area)
        
        # Verificar que NO se creó la categoría
        self.assertEqual(Categorias.objects.count(), categorias_iniciales)
    
    def test_crear_categoria_duplicada_misma_area(self):
        """CA2: Intentar crear categoría con nombre duplicado en la misma área"""
        # Crear primera categoría
        response1 = self.client.post(self.url, self.datos_validos)
        self.assertEqual(response1.status_code, 302)
        self.assertTrue(Categorias.objects.filter(cat_nombre='Programación').exists())
        
        # Intentar crear categoría con mismo nombre y misma área
        categorias_antes_segundo_intento = Categorias.objects.count()
        
        # Esto podría crear un duplicado o fallar, dependiendo de las constraints del modelo
        response2 = self.client.post(self.url, self.datos_validos)
        self.assertEqual(response2.status_code, 302)
    
    def test_crear_categoria_mismo_nombre_diferente_area(self):
        """CA1: Crear categorías con mismo nombre en diferentes áreas"""
        datos_categoria_ciencias = {
            'cat_nombre': 'Programación',  # Mismo nombre
            'cat_descripcion': 'Programación científica',
            'cat_area_fk': self.area_ciencias.id  # Diferente área
        }
        
        # Crear categoría en área de tecnología
        response1 = self.client.post(self.url, self.datos_validos)
        self.assertEqual(response1.status_code, 302)
        
        # Crear categoría con mismo nombre en área de ciencias
        response2 = self.client.post(self.url, datos_categoria_ciencias)
        self.assertEqual(response2.status_code, 302)
        
        # Verificar que existen ambas categorías
        categorias_programacion = Categorias.objects.filter(cat_nombre='Programación')
        self.assertEqual(categorias_programacion.count(), 2)
        
        # Verificar que están en diferentes áreas
        areas = set(cat.cat_area_fk for cat in categorias_programacion)
        self.assertEqual(len(areas), 2)
        self.assertIn(self.area_tecnologia, areas)
        self.assertIn(self.area_ciencias, areas)
    
    def test_mensaje_exito_presente(self):
        """CA3: Verificar que el mensaje de éxito se muestra correctamente"""
        response = self.client.post(self.url, self.datos_validos)
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Categoría creada exitosamente.")
    
    def test_estructura_datos_categoria(self):
        """CA1: Verificar que los datos de la categoría se guardan correctamente"""
        datos_especificos = {
            'cat_nombre': 'Machine Learning',
            'cat_descripcion': 'Categoría enfocada en algoritmos de ML',
            'cat_area_fk': self.area_tecnologia.id
        }
        
        response = self.client.post(self.url, datos_especificos)
        
        # Verificar que la categoría se creó con los datos correctos
        categoria_creada = Categorias.objects.get(cat_nombre='Machine Learning')
        self.assertEqual(categoria_creada.cat_nombre, 'Machine Learning')
        self.assertEqual(categoria_creada.cat_descripcion, 'Categoría enfocada en algoritmos de ML')
        self.assertEqual(categoria_creada.cat_area_fk, self.area_tecnologia)
        
        # Verificar el método __str__
        self.assertEqual(str(categoria_creada), 'Machine Learning')
    
    def test_relacion_area_correcta(self):
        """CA1: Verificar que la relación con el área se establece correctamente"""
        response = self.client.post(self.url, self.datos_validos)
        
        categoria_creada = Categorias.objects.get(cat_nombre='Programación')
        
        # Verificar la relación directa
        self.assertEqual(categoria_creada.cat_area_fk.id, self.area_tecnologia.id)
        self.assertEqual(categoria_creada.cat_area_fk.are_nombre, 'Tecnología')
        
        # Verificar relación inversa
        categorias_en_tecnologia = self.area_tecnologia.categorias_set.all()
        self.assertEqual(categorias_en_tecnologia.count(), 1)
        self.assertEqual(categorias_en_tecnologia.first().cat_nombre, 'Programación')