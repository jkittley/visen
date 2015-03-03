from django import forms


class newVisualisationForm(forms.Form):
    name = forms.CharField(max_length=100)
