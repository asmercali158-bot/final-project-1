from django import forms
from .models import Profile

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'phone_number', 'gpa', 'interested_field', 'preferred_country', 'bio', 'profile_pic']
        
        # Stylizing the form with Bootstrap/Cyber classes
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-primary', 'placeholder': 'Magacaaga oo dhammaystiran'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-primary', 'placeholder': 'Lambarka taleefanka'}),
            'gpa': forms.NumberInput(attrs={'class': 'form-control bg-dark text-white border-primary', 'step': '0.01', 'placeholder': 'GPA (tusaale: 3.5)'}),
            'interested_field': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-primary', 'placeholder': 'Takhasuska (tusaale: IT)'}),
            'preferred_country': forms.TextInput(attrs={'class': 'form-control bg-dark text-white border-primary', 'placeholder': 'Dalka aad rabto'}),
            'bio': forms.Textarea(attrs={'class': 'form-control bg-dark text-white border-primary', 'rows': 3, 'placeholder': 'Inyar naga sii sheeg naftaada...'}),
            'profile_pic': forms.FileInput(attrs={'class': 'form-control bg-dark text-white border-primary'}),
        }

    def clean_gpa(self):
        gpa = self.cleaned_data.get('gpa')
        if gpa < 0 or gpa > 4.0:
            raise forms.ValidationError("Fadlan GPA-gu waa inuu u dhexeeyaa 0 iyo 4.0")
        return gpa