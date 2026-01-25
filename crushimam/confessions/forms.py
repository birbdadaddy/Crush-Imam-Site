from django import forms
from .models import News, ConfessionRequest, HallPost, GradeCalculation


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'body', 'image']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }


class ConfessionRequestForm(forms.ModelForm):
    class Meta:
        model = ConfessionRequest
        fields = ['text', 'anonymous']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 8,
                'placeholder': 'Share your confession here...',
                'class': 'form-control'
            }),
            'anonymous': forms.CheckboxInput(attrs={'class': 'form-checkbox'})
        }
        labels = {
            'text': 'Your Confession',
            'anonymous': 'Post Anonymously'
        }


class HallPostForm(forms.ModelForm):
    class Meta:
        model = HallPost
        fields = ['title', 'body', 'image', 'category']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 6}),
        }


class GradeCalculationForm(forms.Form):
    """Form for calculating student grades in Moroccan system with exams and behavior."""
    
    LEVEL_CHOICES = [
        ('', '--- Khtar mostawa ---'),
        ('5eme', '5ème année'),
        ('1bac', '1ère année BAC'),
        ('2bac', '2ème année BAC'),
    ]
    
    BRANCH_CHOICES_5EME = [
        ('sc', 'Sciences'),
        ('tc', 'Technologies'),
        ('lettres', 'Lettres')
    ]

    BRANCH_CHOICES_1BAC = [
        ('sc_exp', 'Sciences Expérimentales'),
        ('sc_math', 'Sciences Mathématiques'),
        ('sc_telectric', 'Sciences et Technologies Électriques'),
        ('sc_tmechanic', 'Sciences et Technologies Mécaniques'),
        ('sc_econ', 'Sciences Économiques et Gestion'),
        ('lettres', 'Lettres'),
    ]

    BRANCH_CHOICES_2BAC = [
        ('sc_math_a', 'Sciences Mathématiques A'),
        ('sc_math_b', 'Sciences Mathématiques B'),
        ('sc_phys', 'Sciences Physiques'),
        ('sc_svt', 'Sciences de la Vie et de la Terre'),
        ('sc_agronomic', 'Sciences Agronomiques'),
        ('sc_electric', 'Sciences et Technologies Électriques'),
        ('sc_mechanic', 'Sciences et Technologies Mécaniques'),
        ('sc_econ', 'Sciences Économiques'),
        ('sc_humaines', 'Sciences Humaines'),
        ('lettres', 'Lettres'),
    ]
    
    # Define subjects for each level and branch
    SUBJECTS = {
        '5eme': {
            'sc': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'SVT',
                'History & Geography',
                'Islamic Studies',
                'Philosophy',
                'Physical Education',
                'Informatique'
            ],
            'tc': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'Engineering Sciences',
                'History & Geography',
                'Islamic Studies',
                'Philosophy',
                'Physical Education',
                'Informatique'
            ],
            'lettres': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'SVT',
                'History & Geography',
                'Islamic Studies',
                'Philosophy',
                'Physical Education',
            ],
        },
        '1bac': {
            'sc_math': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'SVT',
                'History & Geography',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_exp': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'SVT',
                'History & Geography',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_telectric': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'Engineering Sciences',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_tmechanic': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'Engineering Sciences',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_econ': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Économie et Organisation',
                'Comptabilité',
                'Économie générale et Statistiques',
                'Droit',
                'Informatique de gestion',
                'History & Geography',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'lettres': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'SVT',
                'Philosophy',
                'History & Geography',
                'Islamic Studies',
                'Physical Education'
            ]
        },

        '2bac': {
            'sc_math_a': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'SVT',
                'Islamic Studies',
                'Philosophy',
                'Physical Education',
            ],
            'sc_math_b': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'Engineering Sciences',
                'Islamic Studies',
                'Philosophy',
                'Physical Education',
            ],
            'sc_phys': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_svt': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'SVT',
                'Physics & Chemistry',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_agronomic': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Physics & Chemistry',
                'SVT',
                'SVA',
                'Islamic Studies',
                'Philosophy',
                'History & Geography',
                'Physical Education'
            ],
            'sc_electric': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Engineering Sciences',
                'Physics & Chemistry',
                'Philosophy',
                'Islamic Studies',
                'Physical Education'
            ],
            'sc_mechanic': [
                'Behavior',
                'Arabic',
                'French',
                'English',
                'Mathematics',
                'Engineering Sciences',
                'Physics & Chemistry',
                'Islamic Studies',
                'Philosophy',
                'Physical Education'
            ],
            'sc_econ': [
                'Behavior',
                'Mathematics',
                'Arabic',
                'French',
                'English',
                'Économie et Organisation',
                'Comptabilité',
                'Économie générale et Statistiques',
                'Droit',
                'Informatique de gestion',
                'Philosophy',
                'History & Geography',
                'Islamic Studies',
                'Physical Education'
            ],
            'lettres': [
                'Behavior',
                'Mathematics',
                'Arabic',
                'French',
                'English',
                'Philosophy',
                'History & Geography',
                'Islamic Studies',
                'Physical Education'
            ],
            'sc_humaines': [
                'Behavior',
                'Mathematics',
                'Arabic',
                'French',
                'English',
                'Philosophy',
                'History & Geography',
                'Islamic Studies',
                'Physical Education'
            ]
        }
    }

    
    level = forms.ChoiceField(
        choices=LEVEL_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_level'})
    )
    
    branch = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_branch'})
    )
    
    # Number of exams per subject (1-4)
    num_exams = forms.IntegerField(
        initial=3,
        min_value=1,
        max_value=4,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_num_exams'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set branch choices based on level
        level = self.data.get('level') if self.data else None
        if level == '5eme':
            self.fields['branch'].choices = self.BRANCH_CHOICES_5EME
        elif level == '1bac':
            self.fields['branch'].choices = self.BRANCH_CHOICES_1BAC
        elif level == '2bac':
            self.fields['branch'].choices = self.BRANCH_CHOICES_2BAC
    
    def add_subject_fields(self, level, branch, num_exams=3):
        """Dynamically add fields for each subject with multiple exams and behavior."""
        from .models import GradeCalculation
        
        coefficients = GradeCalculation.SUBJECT_COEFFICIENTS.get(level, {}).get(branch, {})
        
        for subject, coefficient in coefficients.items():
            # Add exam fields
            for exam_num in range(1, int(num_exams) + 1):
                field_name = f'exam_{subject.lower().replace(" ", "_")}_{exam_num}'
                self.fields[field_name] = forms.FloatField(
                    label=f'{subject} - Exam {exam_num}',
                    required=False,
                    min_value=0,
                    max_value=20,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control exam-input',
                        'placeholder': 'Dakhal no9ta (mn 0 l 20)',
                        'data-subject': subject,
                    })
                )
            
            # Add behavior field
            behavior_field_name = f'behavior_{subject.lower().replace(" ", "_")}'
            self.fields[behavior_field_name] = forms.FloatField(
                label=f'{subject} - Comportement/Behavior',
                required=False,
                min_value=0,
                max_value=20,
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'Dakhal no9ta (mn 0 l 20)'
                })
            )
