import unittest
import json
from app import create_app
from core.database import db
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class AuthAPITestCase(unittest.TestCase):
    def setUp(self):
        """Prépare les tests"""
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Créer les tables
        db.create_all()
        
        # Initialiser le système
        from modules.auth.services import ExtendedAuthService
        ExtendedAuthService.init_extended_roles_and_permissions()
    
    def tearDown(self):
        """Nettoie après les tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_health_endpoint(self):
        """Test endpoint de santé"""
        response = self.client.get('/api/auth/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'Extended Auth module running')
        self.assertIn('supported_user_types', data)
    
    def test_login_success(self):
        """Test login avec utilisateur existant"""
        # Login avec utilisateur de test
        response = self.client.post('/api/auth/login', 
            json={
                'username': 'superadmin',
                'password': 'admin123'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['user_type'], 'administrateur')
    
    def test_login_failure(self):
        """Test login avec mauvais credentials"""
        response = self.client.post('/api/auth/login',
            json={
                'username': 'wronguser',
                'password': 'wrongpass'
            },
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_register_with_permission(self):
        """Test enregistrement avec token valide"""
        # D'abord se connecter pour obtenir un token
        login_response = self.client.post('/api/auth/login',
            json={
                'username': 'superadmin', 
                'password': 'admin123'
            },
            content_type='application/json'
        )
        
        login_data = json.loads(login_response.data)
        token = login_data['access_token']
        
        # Ensuite créer un utilisateur
        response = self.client.post('/api/auth/register',
            json={
                'username': 'testuser',
                'email': 'test@test.com',
                'password': 'testpass123',
                'user_type': 'user'
            },
            headers={'Authorization': f'Bearer {token}'},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['user_type'], 'user')
    
    def test_profile_access(self):
        """Test accès au profil"""
        # Login
        login_response = self.client.post('/api/auth/login',
            json={'username': 'superadmin', 'password': 'admin123'},
            content_type='application/json'
        )
        
        token = json.loads(login_response.data)['access_token']
        
        # Accès au profil
        response = self.client.get('/api/auth/profile',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user', data)
        self.assertIn('permissions', data)
    
    def test_user_types_endpoint(self):
        """Test endpoint des types d'utilisateurs"""
        response = self.client.get('/api/auth/user-types')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('user_types', data)
        
        # Vérifier que tous les types sont présents
        types = [ut['type'] for ut in data['user_types']]
        expected_types = ['user', 'administrateur', 'responsable_rh', 'magasinier', 'comptable']
        for expected_type in expected_types:
            self.assertIn(expected_type, types)

if __name__ == '__main__':
    unittest.main()