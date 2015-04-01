from django import forms

from .models import *

__all__ = ['AuthorForm']


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ('name',)
