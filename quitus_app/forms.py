from django import forms
from django.core.validators import RegexValidator
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate
from .models import Quitus, UserProfile

class QuitusForm(forms.ModelForm):
    """Formulaire pour la génération de quitus"""
    
    # Validateur pour le téléphone
    phone_validator = RegexValidator(
        # Accept either +228XXXXXXXX, 228XXXXXXXX, or plain 8 digits (will be normalized)
        regex=r'^(?:\+228|228)?\d{8}$',
        message="Numéro de téléphone invalide. Format attendu : +228XXXXXXXX ou 228XXXXXXXX"
    )
    
    # Validateur pour le numéro de quitus
    quitus_validator = RegexValidator(
        regex=r'^[A-Z0-9\-]+$',
        message="Format invalide. Utilisez uniquement des lettres majuscules, chiffres et tirets."
    )
    
    numero_quitus = forms.CharField(
        label="Numéro de Quitus",
        max_length=50,
        validators=[quitus_validator],
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: PAL-2025-001',
            'class': 'form-control'
        }),
        help_text="Format: PAL-ANNÉE-NUMÉRO"
    )
    
    date_validite = forms.DateField(
        label="Valable jusqu'au",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        help_text="Date de fin de validité du quitus"
    )
    
    nom_prenoms = forms.CharField(
        label="Nom et Prénoms",
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: MENSAH Kofi',
            'class': 'form-control'
        })
    )
    
    raison_sociale = forms.CharField(
        label="Nom / Raison Sociale",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: ENTREPRISE TRANSPORT SARL',
            'class': 'form-control'
        }),
        help_text="Nom de l'entreprise (si applicable)"
    )
    
    cni = forms.CharField(
        label="N° CNI",
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: 123456789',
            'class': 'form-control'
        })
    )
    
    nationalite = forms.CharField(
        label="Nationalité",
        max_length=50,
        initial="Togolaise",
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Togolaise',
            'class': 'form-control'
        })
    )
    
    activite = forms.CharField(
        label="Activité Principale",
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Import-Export',
            'class': 'form-control'
        })
    )
    
    compte_pal = forms.CharField(
        label="N° de Compte PAL",
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: PAL-123456',
            'class': 'form-control'
        })
    )
    
    nif = forms.CharField(
        label="N° d'Identification Fiscale (NIF)",
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: 1234567890',
            'class': 'form-control'
        })
    )
    
    telephone = forms.CharField(
        label="Téléphone Mobile",
        max_length=20,
        widget=forms.TextInput(attrs={
            'placeholder': '+228 XX XX XX XX',
            'class': 'form-control',
            'type': 'tel'
        })
    )
    
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={
            'placeholder': 'exemple@email.com',
            'class': 'form-control'
        })
    )
    
    situation_geo = forms.CharField(
        label="Situation Géographique",
        max_length=300,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: Quartier Administratif, Boulevard de la République',
            'class': 'form-control'
        })
    )
    
    adresse_postale = forms.CharField(
        label="Adresse Postale",
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ex: BP 1234 Lomé',
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = Quitus
        fields = [
            'numero_quitus', 'date_validite', 'nom_prenoms', 'raison_sociale',
            'cni', 'nationalite', 'activite', 'compte_pal', 'nif',
            'telephone', 'email', 'situation_geo', 'adresse_postale'
        ]
    
    def clean_numero_quitus(self):
        """Vérifier l'unicité du numéro de quitus"""
        numero = self.cleaned_data.get('numero_quitus')
        if Quitus.objects.filter(numero_quitus=numero).exists():
            raise forms.ValidationError("Ce numéro de quitus existe déjà.")
        return numero.upper()
    
    def clean_email(self):
        """Nettoyer et valider l'email"""
        email = self.cleaned_data.get('email')
        return email.lower()
    
    def clean_telephone(self):
        """Normalize the telephone to the international format +228XXXXXXXX.

        Behaviour:
        - If user enters 8 digits (e.g. 90123456) -> returns +22890123456
        - If user enters 228XXXXXXXX -> returns +228XXXXXXXX
        - If user enters +228XXXXXXXX -> returns +228XXXXXXXX
        - Otherwise raises ValidationError
        """
        telephone = self.cleaned_data.get('telephone') or ''
        # Keep digits and optional leading +
        raw = ''.join(c for c in telephone if c.isdigit() or c == '+')
        digits = ''.join(c for c in raw if c.isdigit())

        # If user provided a leading +, ensure it's +228XXXXXXXX
        if raw.startswith('+'):
            if digits.startswith('228') and len(digits) == 11:
                return '+' + digits
            raise forms.ValidationError(
                "Numéro de téléphone invalide. Format attendu : +228XXXXXXXX ou 228XXXXXXXX"
            )

        # No leading +: accept 228XXXXXXXX or plain 8 digits
        if digits.startswith('228') and len(digits) == 11:
            return '+' + digits

        if len(digits) == 8:
            return '+228' + digits

        raise forms.ValidationError(
            "Numéro de téléphone invalide. Format attendu : +228XXXXXXXX ou 228XXXXXXXX"
        )


class SearchQuitusForm(forms.Form):
    """Formulaire de recherche avancée de quitus"""
    
    STATUT_CHOICES = [
        ('', 'Tous les statuts'),
        ('VALIDE', 'Valides'),
        ('EXPIRE', 'Expirés'),
        ('ANNULE', 'Annulés'),
    ]
    
    query = forms.CharField(
        label="Recherche",
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Numéro, nom, CNI, raison sociale...',
            'class': 'form-control'
        }),
        help_text="Recherchez par numéro de quitus, nom du bénéficiaire, CNI ou raison sociale"
    )
    
    statut = forms.ChoiceField(
        label="Statut",
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        label="Valable à partir du",
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    date_to = forms.DateField(
        label="Valable jusqu'au",
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    
    def clean(self):
        """Valider la cohérence des dates"""
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                "La date de début ne peut pas être après la date de fin."
            )
        
        return cleaned_data


class LoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé - Authentification par email ou username"""
    
    username = forms.CharField(
        label="Email ou Nom d'utilisateur",
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Votre email ou nom d\'utilisateur',
            'class': 'form-control',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Votre mot de passe',
            'class': 'form-control'
        })
    )
    
    def clean(self):
        """Valider les identifiants - Permettre connexion par email"""
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Essayer d'abord de trouver l'utilisateur par email
            user_by_email = User.objects.filter(email=username).first()
            if user_by_email:
                username = user_by_email.username
            
            # Authentifier
            self.user_cache = authenticate(self.request, username=username, password=password)
            
            if self.user_cache is None:
                raise forms.ValidationError(
                    "Email/Nom d'utilisateur ou mot de passe incorrect.",
                    code='invalid_login',
                )
            else:
                self.confirm_login_allowed(self.user_cache)
        
        return self.cleaned_data


class UserRegistrationForm(forms.ModelForm):
    """Formulaire d'enregistrement utilisateur"""
    
    password1 = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe'
        })
    )
    
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez votre mot de passe'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom'
            }),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        
        return password2
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password and len(password) < 8:
            raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserRoleForm(forms.Form):
    """Formulaire pour créer un utilisateur avec rôle"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin Plateforme - Tous les droits'),
        ('chef', 'Chef de Service/Directeur - Gestion et supervision'),
        ('agent', 'Agent - Créer et gérer les quitus'),
    ]
    
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: jdupont'
        })
    )
    
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'exemple@togoport.tg'
        })
    )
    
    first_name = forms.CharField(
        label="Prénom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Jean'
        })
    )
    
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dupont'
        })
    )
    
    password1 = forms.CharField(
        label='Mot de passe',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Laisser vide pour mot de passe par défaut (TogoPort2024@)'
        }),
        help_text="Au moins 8 caractères. Si vide, le mot de passe par défaut sera assigné."
    )
    
    password2 = forms.CharField(
        label='Confirmer le mot de passe',
        required=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Retapez le mot de passe'
        })
    )
    
    role = forms.ChoiceField(
        label="Rôle",
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        help_text="Définit les permissions de l'utilisateur"
    )
    
    is_active = forms.BooleanField(
        label="Compte actif",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur existe déjà.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email.lower()
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        # Si un mot de passe est fourni, vérifier la correspondance
        if password1 or password2:
            if password1 != password2:
                raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
            
            if password1 and len(password1) < 8:
                raise forms.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        
        return password2
    
    def save(self):
        """Créer l'utilisateur avec le rôle approprié"""
        from django.contrib.auth.models import Group
        
        # Définir le mot de passe par défaut si aucun n'est fourni
        password = self.cleaned_data.get('password1') or 'TogoPort2024@'
        
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=password,
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            is_active=self.cleaned_data.get('is_active', True)
        )
        
        role = self.cleaned_data['role']
        
        # Assigner les permissions selon le rôle
        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'chef':
            user.is_staff = True
            # Ajouter au groupe Chef_Directeur
            try:
                chef_group = Group.objects.get(name='Chef_Directeur')
                user.groups.add(chef_group)
            except Group.DoesNotExist:
                pass
        else:  # agent
            user.is_staff = False
            # Ajouter au groupe Agent
            try:
                agent_group = Group.objects.get(name='Agent')
                user.groups.add(agent_group)
            except Group.DoesNotExist:
                pass
        
        user.save()
        return user


class UserEditForm(forms.ModelForm):
    """Formulaire pour modifier un utilisateur existant"""
    
    ROLE_CHOICES = [
        ('admin', 'Admin Plateforme - Tous les droits'),
        ('chef', 'Chef de Service/Directeur - Gestion et supervision'),
        ('agent', 'Agent - Créer et gérer les quitus'),
    ]
    
    role = forms.ChoiceField(
        label="Rôle",
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            # Déterminer le rôle actuel
            if self.instance.is_superuser:
                self.fields['role'].initial = 'admin'
            elif self.instance.is_staff:
                self.fields['role'].initial = 'chef'
            else:
                self.fields['role'].initial = 'agent'
    
    def save(self, commit=True):
        from django.contrib.auth.models import Group
        
        user = super().save(commit=False)
        role = self.cleaned_data['role']
        
        # Retirer l'utilisateur de tous les groupes existants
        user.groups.clear()
        
        # Mettre à jour les permissions
        if role == 'admin':
            user.is_superuser = True
            user.is_staff = True
        elif role == 'chef':
            user.is_superuser = False
            user.is_staff = True
            # Ajouter au groupe Chef_Directeur
            try:
                chef_group = Group.objects.get(name='Chef_Directeur')
                user.groups.add(chef_group)
            except Group.DoesNotExist:
                pass
        else:  # agent
            user.is_superuser = False
            user.is_staff = False
            # Ajouter au groupe Agent
            try:
                agent_group = Group.objects.get(name='Agent')
                user.groups.add(agent_group)
            except Group.DoesNotExist:
                pass
        
        if commit:
            user.save()
        return user


class PasswordChangeForm(forms.Form):
    """Formulaire pour changer le mot de passe"""
    
    old_password = forms.CharField(
        label='Mot de passe actuel',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez votre mot de passe actuel'
        })
    )
    
    new_password1 = forms.CharField(
        label='Nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le nouveau mot de passe'
        }),
        help_text='Minimum 8 caractères'
    )
    
    new_password2 = forms.CharField(
        label='Confirmer le nouveau mot de passe',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmez le nouveau mot de passe'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """Vérifier que l'ancien mot de passe est correct"""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError('Le mot de passe actuel est incorrect.')
        return old_password
    
    def clean_new_password2(self):
        """Vérifier que les deux nouveaux mots de passe correspondent"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Les deux mots de passe ne correspondent pas.')
            if len(password1) < 8:
                raise forms.ValidationError('Le mot de passe doit contenir au moins 8 caractères.')
        
        return password2
    
    def save(self, commit=True):
        """Sauvegarder le nouveau mot de passe"""
        password = self.cleaned_data.get('new_password1')
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user