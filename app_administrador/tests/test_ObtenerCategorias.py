from django.test import TestCase, Client
from django.urls import reverse
from app_areas.models import Areas
from app_categorias.models import Categorias
from app_administrador.models import Administradores
from app_usuarios.models import Usuario as User
import json


class GetCategoriasTestCase(TestCase):
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        
        # Crear áreas
        self.area_tecnologia = Areas.objects.create(
            are_nombre='Tecnología',
            are_descripcion='Área de tecnología'
        )
        self.area_ciencias = Areas.objects.create(
            are_nombre='Ciencias',
            are_descripcion='Área de ciencias'
        )
        
        # Crear categorías para tecnología
        self.categoria_web = Categorias.objects.create(
            cat_nombre='Desarrollo Web',
            cat_area_fk=self.area_tecnologia
        )
        self.categoria_movil = Categorias.objects.create(
            cat_nombre='Desarrollo Móvil',
            cat_area_fk=self.area_tecnologia
        )
        
        # Crear categorías para ciencias
        self.categoria_fisica = Categorias.objects.create(
            cat_nombre='Física',
            cat_area_fk=self.area_ciencias
        )

    def test_obtener_categorias_por_area_existente(self):
        """Prueba obtener categorías para un área existente con categorías"""
        url = reverse('administrador:get_categorias', args=[self.area_tecnologia.id])
        
        response = self.client.get(url)
        
        # Verificar respuesta exitosa
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Verificar estructura de datos
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)  # 2 categorías para tecnología
        
        # Verificar estructura de cada categoría
        for categoria in data:
            self.assertIn('cat_codigo', categoria)
            self.assertIn('cat_nombre', categoria)
            self.assertIsInstance(categoria['cat_codigo'], int)
            self.assertIsInstance(categoria['cat_nombre'], str)
        
        # Verificar contenidos específicos
        categorias_nombres = [c['cat_nombre'] for c in data]
        self.assertIn('Desarrollo Web', categorias_nombres)
        self.assertIn('Desarrollo Móvil', categorias_nombres)

    def test_obtener_categorias_area_sin_categorias(self):
        """Prueba obtener categorías para un área sin categorías"""
        # Crear área sin categorías
        area_sin_categorias = Areas.objects.create(
            are_nombre='Artes',
            are_descripcion='Área de artes'
        )
        
        url = reverse('administrador:get_categorias', args=[area_sin_categorias.id])
        
        response = self.client.get(url)
        
        # Verificar respuesta exitosa con lista vacía
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])

    def test_obtener_categorias_area_no_existente(self):
        """Prueba obtener categorías para un área que no existe"""
        url = reverse('administrador:get_categorias', args=[99999])  # ID que no existe
        
        response = self.client.get(url)
        
        # Verificar que retorna lista vacía (no error 404)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, [])

    def test_metodo_post_no_permitido(self):
        """Prueba que POST retorne método no permitido"""
        url = reverse('administrador:get_categorias', args=[self.area_tecnologia.id])
        
        response = self.client.post(url)
        
        # Debería retornar 405 Method Not Allowed
        self.assertEqual(response.status_code, 405)

    def test_estructura_datos_categorias(self):
        """Prueba la estructura específica de los datos retornados"""
        url = reverse('administrador:get_categorias', args=[self.area_tecnologia.id])
        
        response = self.client.get(url)
        data = response.json()
        
        # Encontrar una categoría específica
        categoria_web = next((c for c in data if c['cat_nombre'] == 'Desarrollo Web'), None)
        
        self.assertIsNotNone(categoria_web)
        self.assertEqual(categoria_web['cat_codigo'], self.categoria_web.id)
        self.assertEqual(categoria_web['cat_nombre'], 'Desarrollo Web')

    def test_filtrado_correcto_por_area(self):
        """Prueba que el filtrado por área funcione correctamente"""
        # Obtener categorías para tecnología
        url_tecnologia = reverse('administrador:get_categorias', args=[self.area_tecnologia.id])
        response_tecnologia = self.client.get(url_tecnologia)
        categorias_tecnologia = response_tecnologia.json()
        
        # Obtener categorías para ciencias
        url_ciencias = reverse('administrador:get_categorias', args=[self.area_ciencias.id])
        response_ciencias = self.client.get(url_ciencias)
        categorias_ciencias = response_ciencias.json()
        
        # Verificar que son diferentes
        self.assertNotEqual(
            [c['cat_nombre'] for c in categorias_tecnologia],
            [c['cat_nombre'] for c in categorias_ciencias]
        )
        
        # Verificar contenidos específicos
        nombres_tecnologia = [c['cat_nombre'] for c in categorias_tecnologia]
        nombres_ciencias = [c['cat_nombre'] for c in categorias_ciencias]
        
        self.assertIn('Desarrollo Web', nombres_tecnologia)
        self.assertIn('Desarrollo Móvil', nombres_tecnologia)
        self.assertIn('Física', nombres_ciencias)
        
        self.assertNotIn('Física', nombres_tecnologia)
        self.assertNotIn('Desarrollo Web', nombres_ciencias)
