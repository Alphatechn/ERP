from app import create_app, db
from backend.modules.auth.models import User
from backend.modules.auth.services import AuthService
from backend.modules.rh.models import Department, Employee
from datetime import date

def init_database():
    """Initialise la base de données avec des données de test"""
    app = create_app()
    
    with app.app_context():
        # Créer les tables
        db.create_all()
        
        # Créer un utilisateur administrateur
        admin_data = {
            'username': 'admin',
            'email': 'admin@erp.com',
            'password': 'admin123',
            'first_name': 'Administrateur',
            'last_name': 'Système',
            'role': 'admin'
        }
        
        try:
            AuthService.register_user(admin_data)
            print("✅ Utilisateur administrateur créé")
        except ValueError as e:
            print(f"⚠️  Utilisateur administrateur déjà existant: {e}")
        
        # Créer des départements
        departments = [
            {
                'name': 'Direction Générale',
                'description': 'Direction générale de l\'entreprise'
            },
            {
                'name': 'Ressources Humaines',
                'description': 'Gestion des ressources humaines'
            },
            {
                'name': 'Comptabilité',
                'description': 'Gestion comptable et financière'
            },
            {
                'name': 'Commercial',
                'description': 'Service commercial et ventes'
            },
            {
                'name': 'Technique',
                'description': 'Service technique et développement'
            }
        ]
        
        for dept_data in departments:
            dept = Department.query.filter_by(name=dept_data['name']).first()
            if not dept:
                dept = Department(**dept_data)
                db.session.add(dept)
                print(f"✅ Département '{dept_data['name']}' créé")
        
        db.session.commit()
        
        # Créer quelques employés de test
        employees_data = [
            {
                'username': 'manager_rh',
                'email': 'rh@erp.com',
                'password': 'password123',
                'first_name': 'Marie',
                'last_name': 'Dupont',
                'role': 'manager',
                'employee_number': 'EMP001',
                'position': 'Responsable RH',
                'hire_date': date(2020, 1, 15),
                'salary': 45000.00,
                'contract_type': 'CDI'
            },
            {
                'username': 'comptable',
                'email': 'compta@erp.com',
                'password': 'password123',
                'first_name': 'Pierre',
                'last_name': 'Martin',
                'role': 'user',
                'employee_number': 'EMP002',
                'position': 'Comptable',
                'hire_date': date(2021, 3, 1),
                'salary': 35000.00,
                'contract_type': 'CDI'
            },
            {
                'username': 'commercial',
                'email': 'commercial@erp.com',
                'password': 'password123',
                'first_name': 'Sophie',
                'last_name': 'Bernard',
                'role': 'user',
                'employee_number': 'EMP003',
                'position': 'Commercial',
                'hire_date': date(2021, 6, 10),
                'salary': 38000.00,
                'contract_type': 'CDI'
            }
        ]
        
        for emp_data in employees_data:
            # Créer l'utilisateur
            user_data = {k: v for k, v in emp_data.items() if k in ['username', 'email', 'password', 'first_name', 'last_name', 'role']}
            try:
                AuthService.register_user(user_data)
                user = User.query.filter_by(username=user_data['username']).first()
                
                # Créer l'employé
                dept = Department.query.filter_by(name='Ressources Humaines').first()
                if emp_data['position'] == 'Comptable':
                    dept = Department.query.filter_by(name='Comptabilité').first()
                elif emp_data['position'] == 'Commercial':
                    dept = Department.query.filter_by(name='Commercial').first()
                
                employee = Employee(
                    employee_number=emp_data['employee_number'],
                    user_id=user.id,
                    department_id=dept.id if dept else None,
                    position=emp_data['position'],
                    hire_date=emp_data['hire_date'],
                    salary=emp_data['salary'],
                    contract_type=emp_data['contract_type']
                )
                db.session.add(employee)
                print(f"✅ Employé '{emp_data['first_name']} {emp_data['last_name']}' créé")
                
            except ValueError as e:
                print(f"⚠️  Employé déjà existant: {e}")
        
        db.session.commit()
        print("\n🎉 Base de données initialisée avec succès!")
        print("\n📋 Comptes de test créés:")
        print("   - Admin: admin / admin123")
        print("   - RH: manager_rh / password123")
        print("   - Comptable: comptable / password123")
        print("   - Commercial: commercial / password123")
        print("\n🔐 Authentification basée sur Flask-Login (sessions)")
        print("   - Utilisez les cookies de session pour l'authentification")
        print("   - Option 'remember' disponible pour les sessions longues")

if __name__ == '__main__':
    init_database() 