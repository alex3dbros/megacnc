from django import forms


class CreateProject(forms.Form):
    project_name = forms.CharField(label="Project Name", max_length=100)