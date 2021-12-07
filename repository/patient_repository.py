class PatientRepository:
    def __init__(self):
        self.mockDatabase = []
    def add(self, element):
        self.mockDatabase.append(element)
    def delete(self, id):
        self.mockDatabase.pop(id)
    def get(self, id):
        return self.mockDatabase[id]
    def getAll(self):
        return self.mockDatabase