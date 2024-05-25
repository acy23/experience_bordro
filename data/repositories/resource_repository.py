from data.entities.resource import Resource
from extensions import db

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

    def update(self, resource_id, data):
        resource = self.find_by_id(resource_id)
        if resource:
            resource.userid = data.get('userid', resource.userid)
            resource.pdf_data = data.get('pdf_data', resource.pdf_data)
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
