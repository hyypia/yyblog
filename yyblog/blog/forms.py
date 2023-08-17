from django import forms
from .models import Comment


class SearchForm(forms.Form):
    query = forms.CharField(label="")


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["name", "email", "body"]
