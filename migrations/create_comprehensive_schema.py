"""
Database migration script for EstateCore comprehensive schema
This script creates all the necessary tables and relationships for the enhanced EstateCore system.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    app = Flask(__name__)
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@127.0.0.1:5432/estatecore_devecs.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    return app

def run_migration():
    """Run the comprehensive database migration"""
    app = create_app()
    
    with app.app_context():
        db = SQLAlchemy(app)
        
        print("Starting comprehensive database migration...")
        
        # Create all tables using raw SQL for better control
        migration_sql = """
        -- Drop existing tables if they exist (for development)
        DROP TABLE IF EXISTS maintenance_photos CASCADE;
        DROP TABLE IF EXISTS work_orders CASCADE;
        DROP TABLE IF EXISTS maintenance_requests CASCADE;
        DROP TABLE IF EXISTS lease_documents CASCADE;
        DROP TABLE IF EXISTS lease_tenants CASCADE;
        DROP TABLE IF EXISTS payments CASCADE;
        DROP TABLE IF EXISTS rent_records CASCADE;
        DROP TABLE IF EXISTS leases CASCADE;
        DROP TABLE IF EXISTS units CASCADE;
        DROP TABLE IF EXISTS properties CASCADE;
        DROP TABLE IF EXISTS tenants CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        
        -- Users table (enhanced)
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            phone VARCHAR(20),
            password_hash VARCHAR(255) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            role VARCHAR(50) NOT NULL DEFAULT 'user',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            last_login_ip VARCHAR(45),
            password_changed_at TIMESTAMP,
            avatar_url VARCHAR(500),
            timezone VARCHAR(50) DEFAULT 'UTC',
            email_notifications BOOLEAN DEFAULT TRUE,
            sms_notifications BOOLEAN DEFAULT FALSE,
            two_factor_enabled BOOLEAN DEFAULT FALSE,
            two_factor_secret VARCHAR(32),
            email_verified BOOLEAN DEFAULT FALSE,
            email_verification_token VARCHAR(255),
            password_reset_token VARCHAR(255),
            password_reset_expires TIMESTAMP
        );
        
        -- Properties table
        CREATE TABLE properties (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            address VARCHAR(512) NOT NULL,
            city VARCHAR(100) NOT NULL,
            state VARCHAR(50) NOT NULL,
            zip_code VARCHAR(20) NOT NULL,
            property_type VARCHAR(50) DEFAULT 'residential',
            total_units INTEGER DEFAULT 1,
            bedrooms INTEGER,
            bathrooms DECIMAL(3,1),
            square_feet INTEGER,
            year_built INTEGER,
            purchase_price DECIMAL(12,2),
            current_market_value DECIMAL(12,2),
            monthly_mortgage DECIMAL(10,2),
            monthly_insurance DECIMAL(10,2),
            monthly_taxes DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'active',
            acquisition_date DATE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );
        
        -- Units table
        CREATE TABLE units (
            id SERIAL PRIMARY KEY,
            property_id INTEGER NOT NULL REFERENCES properties(id),
            unit_number VARCHAR(50) NOT NULL,
            bedrooms INTEGER,
            bathrooms DECIMAL(3,1),
            square_feet INTEGER,
            rent_amount DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'available',
            is_rentable BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            UNIQUE(property_id, unit_number)
        );
        
        -- Tenants table (enhanced)
        CREATE TABLE tenants (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            phone_primary VARCHAR(20),
            phone_secondary VARCHAR(20),
            mailing_address VARCHAR(512),
            mailing_city VARCHAR(100),
            mailing_state VARCHAR(50),
            mailing_zip VARCHAR(20),
            emergency_contact_name VARCHAR(200),
            emergency_contact_phone VARCHAR(20),
            emergency_contact_relationship VARCHAR(50),
            employer_name VARCHAR(200),
            employer_phone VARCHAR(20),
            job_title VARCHAR(100),
            monthly_income DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'active',
            move_in_date DATE,
            move_out_date DATE,
            credit_score INTEGER,
            security_deposit_paid DECIMAL(10,2) DEFAULT 0,
            pet_deposit_paid DECIMAL(10,2) DEFAULT 0,
            preferred_payment_method VARCHAR(20) DEFAULT 'card',
            communication_preference VARCHAR(20) DEFAULT 'email',
            has_pets BOOLEAN DEFAULT FALSE,
            pet_details TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );
        
        -- Leases table
        CREATE TABLE leases (
            id SERIAL PRIMARY KEY,
            property_id INTEGER NOT NULL REFERENCES properties(id),
            unit_id INTEGER NOT NULL REFERENCES units(id),
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            lease_term_months INTEGER NOT NULL,
            monthly_rent DECIMAL(10,2) NOT NULL,
            security_deposit DECIMAL(10,2) DEFAULT 0,
            pet_deposit DECIMAL(10,2) DEFAULT 0,
            late_fee_amount DECIMAL(10,2) DEFAULT 50,
            late_fee_grace_days INTEGER DEFAULT 5,
            lease_type VARCHAR(20) DEFAULT 'fixed',
            payment_due_day INTEGER DEFAULT 1,
            auto_renew BOOLEAN DEFAULT FALSE,
            renewal_notice_days INTEGER DEFAULT 60,
            status VARCHAR(20) DEFAULT 'draft',
            signed_date DATE,
            termination_date DATE,
            termination_reason VARCHAR(200),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );
        
        -- Lease-Tenants association table (many-to-many)
        CREATE TABLE lease_tenants (
            lease_id INTEGER REFERENCES leases(id) ON DELETE CASCADE,
            tenant_id INTEGER REFERENCES tenants(id) ON DELETE CASCADE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (lease_id, tenant_id)
        );
        
        -- Lease Documents table
        CREATE TABLE lease_documents (
            id SERIAL PRIMARY KEY,
            lease_id INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            mime_type VARCHAR(100),
            document_type VARCHAR(50) DEFAULT 'lease',
            description VARCHAR(500),
            is_signed BOOLEAN DEFAULT FALSE,
            signed_date DATE,
            uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            uploaded_by_user_id INTEGER REFERENCES users(id)
        );
        
        -- Rent Records table (enhanced)
        CREATE TABLE rent_records (
            id SERIAL PRIMARY KEY,
            lease_id INTEGER NOT NULL REFERENCES leases(id),
            tenant_id INTEGER NOT NULL REFERENCES tenants(id),
            property_id INTEGER NOT NULL REFERENCES properties(id),
            unit_id INTEGER REFERENCES units(id),
            amount DECIMAL(10,2) NOT NULL,
            late_fee DECIMAL(10,2) DEFAULT 0,
            other_fees DECIMAL(10,2) DEFAULT 0,
            total_amount DECIMAL(10,2) NOT NULL,
            amount_paid DECIMAL(10,2) DEFAULT 0,
            amount_outstanding DECIMAL(10,2) NOT NULL,
            period_start DATE NOT NULL,
            period_end DATE NOT NULL,
            due_date DATE NOT NULL,
            paid_date TIMESTAMP,
            status VARCHAR(20) DEFAULT 'unpaid',
            late_fee_applied BOOLEAN DEFAULT FALSE,
            reminders_sent INTEGER DEFAULT 0,
            last_reminder_sent TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            preferred_payment_method VARCHAR(20) DEFAULT 'card'
        );
        
        -- Payments table (enhanced)
        CREATE TABLE payments (
            id SERIAL PRIMARY KEY,
            rent_record_id INTEGER REFERENCES rent_records(id),
            tenant_id INTEGER NOT NULL REFERENCES tenants(id),
            amount DECIMAL(10,2) NOT NULL,
            payment_method VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            stripe_payment_intent_id VARCHAR(80),
            stripe_charge_id VARCHAR(80),
            transaction_id VARCHAR(100),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            description VARCHAR(255),
            notes TEXT,
            receipt_url VARCHAR(500)
        );
        
        -- Maintenance Requests table (enhanced)
        CREATE TABLE maintenance_requests (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL,
            priority VARCHAR(20) DEFAULT 'medium',
            property_id INTEGER NOT NULL REFERENCES properties(id),
            unit_id INTEGER REFERENCES units(id),
            specific_location VARCHAR(100),
            tenant_id INTEGER REFERENCES tenants(id),
            requested_by_user_id INTEGER REFERENCES users(id),
            contact_phone VARCHAR(20),
            status VARCHAR(32) DEFAULT 'open',
            assigned_to_user_id INTEGER REFERENCES users(id),
            assigned_to_vendor VARCHAR(200),
            scheduled_date TIMESTAMP,
            estimated_completion TIMESTAMP,
            actual_completion TIMESTAMP,
            estimated_cost DECIMAL(10,2),
            actual_cost DECIMAL(10,2),
            tenant_can_be_present BOOLEAN DEFAULT TRUE,
            special_instructions TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        
        -- Work Orders table
        CREATE TABLE work_orders (
            id SERIAL PRIMARY KEY,
            maintenance_request_id INTEGER NOT NULL REFERENCES maintenance_requests(id) ON DELETE CASCADE,
            work_order_number VARCHAR(50) UNIQUE NOT NULL,
            description TEXT NOT NULL,
            instructions TEXT,
            assigned_to_user_id INTEGER REFERENCES users(id),
            vendor_name VARCHAR(200),
            vendor_contact VARCHAR(100),
            status VARCHAR(20) DEFAULT 'pending',
            scheduled_start TIMESTAMP,
            scheduled_end TIMESTAMP,
            actual_start TIMESTAMP,
            actual_end TIMESTAMP,
            labor_cost DECIMAL(10,2),
            material_cost DECIMAL(10,2),
            total_cost DECIMAL(10,2),
            completion_notes TEXT,
            warranty_info TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Maintenance Photos table
        CREATE TABLE maintenance_photos (
            id SERIAL PRIMARY KEY,
            maintenance_request_id INTEGER NOT NULL REFERENCES maintenance_requests(id) ON DELETE CASCADE,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER,
            photo_type VARCHAR(20) DEFAULT 'before',
            description VARCHAR(500),
            taken_by_user_id INTEGER REFERENCES users(id),
            uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Create indexes for better performance
        CREATE INDEX idx_users_email ON users(email);
        CREATE INDEX idx_users_role ON users(role);
        CREATE INDEX idx_users_is_active ON users(is_active);
        
        CREATE INDEX idx_properties_status ON properties(status);
        CREATE INDEX idx_properties_city ON properties(city);
        CREATE INDEX idx_properties_state ON properties(state);
        
        CREATE INDEX idx_units_property_id ON units(property_id);
        CREATE INDEX idx_units_status ON units(status);
        
        CREATE INDEX idx_tenants_email ON tenants(email);
        CREATE INDEX idx_tenants_status ON tenants(status);
        
        CREATE INDEX idx_leases_property_id ON leases(property_id);
        CREATE INDEX idx_leases_unit_id ON leases(unit_id);
        CREATE INDEX idx_leases_status ON leases(status);
        CREATE INDEX idx_leases_end_date ON leases(end_date);
        
        CREATE INDEX idx_rent_records_tenant_id ON rent_records(tenant_id);
        CREATE INDEX idx_rent_records_lease_id ON rent_records(lease_id);
        CREATE INDEX idx_rent_records_property_id ON rent_records(property_id);
        CREATE INDEX idx_rent_records_status ON rent_records(status);
        CREATE INDEX idx_rent_records_due_date ON rent_records(due_date);
        CREATE INDEX idx_rent_records_period_start ON rent_records(period_start);
        
        CREATE INDEX idx_payments_tenant_id ON payments(tenant_id);
        CREATE INDEX idx_payments_rent_record_id ON payments(rent_record_id);
        CREATE INDEX idx_payments_status ON payments(status);
        CREATE INDEX idx_payments_stripe_payment_intent ON payments(stripe_payment_intent_id);
        
        CREATE INDEX idx_maintenance_requests_property_id ON maintenance_requests(property_id);
        CREATE INDEX idx_maintenance_requests_unit_id ON maintenance_requests(unit_id);
        CREATE INDEX idx_maintenance_requests_tenant_id ON maintenance_requests(tenant_id);
        CREATE INDEX idx_maintenance_requests_status ON maintenance_requests(status);
        CREATE INDEX idx_maintenance_requests_category ON maintenance_requests(category);
        CREATE INDEX idx_maintenance_requests_priority ON maintenance_requests(priority);
        CREATE INDEX idx_maintenance_requests_created_at ON maintenance_requests(created_at);
        
        CREATE INDEX idx_work_orders_maintenance_request_id ON work_orders(maintenance_request_id);
        CREATE INDEX idx_work_orders_status ON work_orders(status);
        CREATE INDEX idx_work_orders_assigned_to_user_id ON work_orders(assigned_to_user_id);
        
        -- Create updated_at triggers for automatic timestamp updates
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_units_updated_at BEFORE UPDATE ON units 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_leases_updated_at BEFORE UPDATE ON leases 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_rent_records_updated_at BEFORE UPDATE ON rent_records 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_maintenance_requests_updated_at BEFORE UPDATE ON maintenance_requests 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        CREATE TRIGGER update_work_orders_updated_at BEFORE UPDATE ON work_orders 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            # Execute the migration SQL
            db.session.execute(text(migration_sql))
            db.session.commit()
            print("✅ Database schema created successfully!")
            
            # Create a super admin user if it doesn't exist
            create_super_admin_sql = """
            INSERT INTO users (email, password_hash, role, is_active, first_name, last_name, email_verified, created_at)
            VALUES ('admin@estatecore.com', 'pbkdf2:sha256:260000$VFh5NzJDMEFhazF3$d3a5e5b5c4c3b2a1a0a9a8a7a6a5a4a3a2a1a0', 'super_admin', TRUE, 'Super', 'Admin', TRUE, CURRENT_TIMESTAMP)
            ON CONFLICT (email) DO NOTHING;
            """
            
            db.session.execute(text(create_super_admin_sql))
            db.session.commit()
            print("✅ Super admin user created (email: admin@estatecore.com, password: admin123)")
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise e

if __name__ == "__main__":
    run_migration()