from data.entities.resource import Resource
from extensions import db

from datetime import date, timedelta
from datetime import datetime

class ResourceRepository:

    def create(self, data):
        new_resource = Resource(
            userid=data['userid'],
            pdf_data=data['pdf_data']
        )
        db.session.add(new_resource)
        db.session.commit()
        return new_resource

    def find_by_id(self, resource_id):
        return Resource.query.filter_by(id=resource_id).first()
    
    def get_payroll_by_userId(self, user_id):

        today = date.today()
        start_of_month = datetime(today.year, today.month, 1)
        end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)

        payroll = Resource.query.filter(
            Resource.userid == user_id,
            
            Resource.created_at >= start_of_month,
            Resource.created_at <= end_of_month,
        ).first()

        if payroll is None:
            return {}
        
        return payroll

    def is_payroll_read(self, user_id):

        today = date.today()
        start_of_month = datetime(today.year, today.month, 1)
        end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)

        payroll = Resource.query.filter(
            Resource.userid == user_id,
            
            Resource.created_at >= start_of_month,
            Resource.created_at <= end_of_month,
        ).first()

        if payroll is None:
            return False
        
        if payroll.is_read != True:
            return False

        return True

    def update(self, resource_id, data):
        resource = self.find_by_id(resource_id)
        if resource:
            resource.userid = data.get('userid', resource.userid)
            resource.pdf_data = data.get('pdf_data', resource.pdf_data)
            resource.is_read = data.get('is_read', resource.is_read)
            db.session.commit()
            return resource
        return None

    def delete(self, resource_id):
        resource = self.find_by_id(resource_id)
        if resource:
            db.session.delete(resource)
            db.session.commit()
            return True
        return False
