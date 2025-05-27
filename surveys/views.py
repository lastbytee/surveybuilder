from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.views.decorators.http import require_POST
from django.http import HttpResponseBadRequest
from .models import Survey, Question, Response, Answer ,Contact
from django.http import HttpResponse
from django.contrib import messages
import openpyxl
from collections import defaultdict, Counter
from .forms import ContactForm
from django.http import JsonResponse
from django.db.models import Count
from datetime import datetime
import json
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .forms import SignUpForm, EmailAuthenticationForm
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator



def home(request):
    return render(request, 'home.html')


@login_required
def dashboard(request):
    province_choices = [
        ('Kigali', 'Kigali'),
        ('Eastern', 'Eastern'),
        ('Western', 'Western'),
        ('Northern', 'Northern'),
        ('Southern', 'Southern'),
    ]

    surveys = Survey.objects.filter(created_by=request.user)

    # Filtering logic
    title = request.GET.get('title')
    location = request.GET.get('location')
    province = request.GET.get('province')  # <-- new filter
    date = request.GET.get('date')

    if title:
        surveys = surveys.filter(title__icontains=title)
    if location:
        surveys = surveys.filter(location__icontains=location)
    if province:
        surveys = surveys.filter(province=province)
    if date:
        surveys = surveys.filter(created_at__date=date)

    # Chart data: count surveys by day
    survey_counts = (
        surveys.extra({'day': "date(created_at)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    if survey_counts:
        chart_data = [int(sc['count']) for sc in survey_counts]
        chart_labels = [
            datetime.strptime(sc['day'], '%Y-%m-%d').strftime('%Y-%m-%d')
            for sc in survey_counts
        ]
    else:
        chart_data = []
        chart_labels = []

    context = {
        'surveys': surveys,
        'province_choices': province_choices,  # pass province choices for template
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def create_survey(request):
    if request.method == 'GET':
        components = [
            ('text', 'Short Text'),
            ('textarea', 'Long Text'),
            ('dropdown', 'Dropdown'),
            ('checkbox', 'Checkbox'),
            ('radio', 'Radio'),
            ('rating', 'Rating'),
            ('yesno', 'Yes/No'),
            ('date', 'Date'),
        ]
        return render(request, 'survey_builder.html', {'components': components})

    if request.method == 'POST' and request.headers.get('Content-Type') == 'application/json':
        try:
            data = json.loads(request.body)
            title = data.get('title')
            description = data.get('description')
            location = data.get('location') 
            province = data.get('province')  
            fields = data.get('fields', [])

            if not title or not isinstance(fields, list):
                return JsonResponse({'error': 'Invalid input'}, status=400)

            survey = Survey.objects.create(
                title=title,
                description=description or '',
                location=location or '',   # ⬅️ pass location
                province=province or '',   # ⬅️ pass province
                created_by=request.user
            )

            for field in fields:
                label = field.get('label')
                qtype = field.get('type')
                required = field.get('required', False)
                options = field.get('options')

                if not label or not qtype:
                    continue

                if isinstance(options, list):
                    options_str = ','.join(options)
                elif isinstance(options, dict):
                    options_str = json.dumps(options)
                elif isinstance(options, str):
                    options_str = options
                else:
                    options_str = ''

                Question.objects.create(
                    survey=survey,
                    label=label,
                    question_type=qtype,
                    required=required,
                    options=options_str
                )

            return JsonResponse({'message': 'Survey saved successfully'})

        except Exception as e:
            print("Error saving survey:", e)
            return JsonResponse({'error': 'Failed to save survey'}, status=400)

@login_required
def survey_detail(request, pk):
    survey = get_object_or_404(Survey, pk=pk, created_by=request.user)
    return render(request, 'mysurvey.html', {'survey': survey})


def take_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk)
    questions = survey.questions.all()

    if request.method == 'POST':
        response = Response.objects.create(survey=survey)
        for question in questions:
            ans = request.POST.getlist(f'q{question.id}')  
            Answer.objects.create(
                response=response,
                question=question,
                answer_text=", ".join(ans)
            )
        return redirect('thank_you')

    # Split options in advance
    for question in questions:
        if question.options:
            question.split_options = [opt.strip() for opt in question.options.split(',')]
        else:
            question.split_options = []

    return render(request, 'take_survey.html', {
        'survey': survey,
        'questions': questions
    })
def thank_you(request):
    return render(request, 'thank_you.html')

def view_responses(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    responses = survey.responses.all()
    questions = survey.questions.all()

    all_answers = Answer.objects.filter(response__survey=survey)
    
    # Bar chart summary: answers per question
    question_labels = [q.label for q in questions]
    count_by_question = Counter(ans.question.label for ans in all_answers)
    response_counts = [count_by_question.get(label, 0) for label in question_labels]

    # Prepare per-question chart data for choice-based questions
    charts_data = []

    for question in questions:
        if question.question_type in ['multiple_choice', 'dropdown', 'checkbox', 'yes_no']:
            answer_counts = defaultdict(int)
            question_answers = all_answers.filter(question=question)

            for answer in question_answers:
                if question.question_type == 'checkbox':
                    # Assume checkbox answers are stored as comma-separated
                    for val in answer.answer_text.split(','):
                        answer_counts[val.strip()] += 1
                else:
                    answer_counts[answer.answer_text.strip()] += 1

            charts_data.append({
                'label': question.label,
                'options': list(answer_counts.keys()),
                'counts': list(answer_counts.values()),
                'chartType': 'pie' if question.question_type == 'yes_no' else 'bar'
            })

    context = {
        'survey': survey,
        'responses': responses,
        'questions': json.dumps(question_labels),
        'response_counts': json.dumps(response_counts),
        'charts_data': json.dumps(charts_data),
    }
    return render(request, 'response.html', context)

def export_to_excel(request, survey_id):
    survey = Survey.objects.get(id=survey_id)
    responses = survey.responses.all()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Responses"

    # Header row
    question_labels = [q.label for q in survey.questions.all()]
    ws.append(['Submitted At'] + question_labels)

    for response in responses:
        row = [response.submitted_at.strftime("%Y-%m-%d %H:%M")]
        answers = {a.question.label: a.answer_text for a in response.answers.all()}
        row += [answers.get(label, "") for label in question_labels]
        ws.append(row)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=survey_{survey_id}_responses.xlsx'
    wb.save(response)
    return response

def delete_survey(request, pk):
    survey = get_object_or_404(Survey, pk=pk, created_by=request.user)
    if request.method == 'POST':
        survey.delete()
        return redirect('dashboard')
    
def mysurvey(request):
    query = request.GET.get('q', '')
    surveys = Survey.objects.filter(created_by=request.user)
    if query:
        surveys = surveys.filter(title__icontains=query)

    paginator = Paginator(surveys, 5)
    page_number = request.GET.get('page')
    surveys_page = paginator.get_page(page_number)

    return render(request, 'mysurvey.html', {
        'surveys': surveys_page,
        'query': query  # Pass the query back to retain the search term
    })
#account settings

def login(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'login.html', {'form': form})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def logout(request):
    auth_logout(request)
    return redirect('home')

#edit survey#########################
@login_required
def edit_survey(request, survey_id):
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    questions = survey.questions.all()

    if request.method == 'POST':
        survey.title = request.POST.get('title')
        survey.description = request.POST.get('description')
        survey.save()

    
        for question in questions:
            if request.POST.get(f'delete_question_{question.id}') == '1':
                question.delete()
                continue

            label = request.POST.get(f'question_label_{question.id}')
            qtype = request.POST.get(f'question_type_{question.id}')
            options_raw = request.POST.get(f'question_options_{question.id}')

            if label and qtype:
                question.label = label
                question.question_type = qtype
                question.options = [opt.strip() for opt in options_raw.split(',')] if options_raw else []
                question.save()

        
        for key in request.POST:
            if key.startswith('new_question_label_'):
                suffix = key.split('new_question_label_')[1]
                label = request.POST.get(f'new_question_label_{suffix}')
                qtype = request.POST.get(f'new_question_type_{suffix}')
                options_raw = request.POST.get(f'new_question_options_{suffix}')

                if label and qtype:
                    survey.questions.create(
                        label=label,
                        question_type=qtype,
                        options=[opt.strip() for opt in options_raw.split(',')] if options_raw else []
                    )

        return redirect('mysurvey')

    return render(request, 'edit_survey.html',{
        'survey': survey,
        'questions': questions,
        })

def about(request):
    return render(request, 'about.html')

def contact(request):
    success = False
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save to database
            Contact.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                message=form.cleaned_data['message']
            )
            success = True
            form = ContactForm()  # Reset the form
    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form, 'success': success})

#template view
@login_required
def survey_template(request):
    components = [
        ('text', 'Text'),
        ('textarea', 'Textarea'),
        ('rating', 'Rating'),
        ('yesno', 'Yes/No'),
        ('dropdown', 'Dropdown'),
        ('checkbox', 'Checkbox'),
        ('radio', 'Radio'),
        ('date', 'Date'),
    ]

    if request.method == 'POST':
        title = request.POST.get('survey_title')
        location = request.POST.get('location')
        province = request.POST.get('province')
        labels = request.POST.getlist('question_label')
        types = request.POST.getlist('question_type')

        if title and location and province and labels and types:
            survey = Survey.objects.create(
                title=title,
                location=location,
                province=province,
                created_by=request.user,
                description="Created from template"
            )

            for label, qtype in zip(labels, types):
                Question.objects.create(
                    survey=survey,
                    label=label,
                    question_type=qtype,
                    required=False,
                    options=""  # Empty by default
                )

            return redirect('mysurvey')  # Ensure this URL name is defined in urls.py

    # Default sample questions
    sample_questions = [
        {'label': 'How would you rate our product?', 'question_type': 'rating'},
        {'label': 'What feature do you use the most?', 'question_type': 'text'},
        {'label': 'Would you recommend us to others?', 'question_type': 'yesno'},
    ]

    return render(request, 'template.html', {
        'components': components,
        'sample_questions': sample_questions
    })