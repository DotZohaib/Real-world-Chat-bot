from datetime import datetime
from app import db

class Entry(db.Model):
    """Model for knowledge base entries."""
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    tags = db.Column(db.Text)  # Comma-separated tags
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Entry {self.id}: {self.question[:30]}...>'
    
    @property
    def tag_list(self):
        """Return tags as a list."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',')]
    
    def to_dict(self):
        """Convert the entry to a dictionary."""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'tags': self.tag_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }