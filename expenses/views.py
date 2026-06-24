from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum
from .models import Category, Expense
from datetime import timedelta

class UserRegisterView(CreateView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('dashboard') # dashboardga o'tib ketadi

class UserLoginView(LoginView):
    template_name = 'registration/login.html'

class UserLogoutView(LogoutView):
    next_page = 'login'

@login_required
def dashboard_view(request):
    user = request.user
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # Statistika querylari
    today_total = Expense.objects.filter(user=user, date=today).aggregate(total=Sum('amount'))['total'] or 0
    week_total = Expense.objects.filter(user=user, date__gte=start_of_week).aggregate(total=Sum('amount'))['total'] or 0
    month_total = Expense.objects.filter(user=user, date__gte=start_of_month).aggregate(total=Sum('amount'))['total'] or 0

    # Kategoriya bo'yicha guruhlash (Chart.js uchun)
    category_data = Expense.objects.filter(user=user).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    most_expensive_category = category_data[0]['category__name'] if category_data else "Mavjud emas"

    # Grafik uchun ma'lumotlarni tayyorlash
    chart_labels = [item['category__name'] for item in category_data]
    chart_values = [float(item['total']) for item in category_data]

    context = {
        'today_total': today_total,
        'week_total': week_total,
        'month_total': month_total,
        'most_expensive_category': most_expensive_category,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
    }
    return render(request, 'expenses/dashboard.html', context)

# === KATEGORIYA CRUD ===
@login_required
def category_list_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            Category.objects.create(name=name, user=request.user)
        return redirect('category_list')
    
    categories = Category.objects.filter(user=request.user)
    return render(request, 'expenses/category_list.html', {'categories': categories})

@login_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk, user=request.user)
    category.delete()
    return redirect('category_list')

# === XARAJATLAR CRUD ===
@login_required
def expense_list(request):
    user = request.user
    expenses = Expense.objects.filter(user=user).order_by('-date')
    categories = Category.objects.filter(user=user)

    # Filtrlash logikasi
    filter_type = request.GET.get('filter_type')
    cat_filter = request.GET.get('category')
    today = timezone.now().date()

    if filter_type == 'today':
        expenses = expenses.filter(date=today)
    elif filter_type == 'week':
        expenses = expenses.filter(date__gte=today - timedelta(days=7))
    elif filter_type == 'month':
        expenses = expenses.filter(date__month=today.month)

    if cat_filter:
        expenses = expenses.filter(category_id=cat_filter)

    return render(request, 'expenses/expense_list.html', {'expenses': expenses, 'categories': categories})

@login_required
def expense_create(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        date = request.POST.get('date') or timezone.now().date()
        
        category = get_object_or_404(Category, id=category_id, user=request.user)
        Expense.objects.create(
            category=category, amount=amount, description=description, date=date, user=request.user
        )
        return redirect('expense_list')
    
    categories = Category.objects.filter(user=request.user)
    return render(request, 'expenses/expense_form.html', {'categories': categories})

# === YANGI: XARAJATLARNI TAHRIRLASH FUNKSIYASI ===
@login_required
def expense_update(request, pk):
    # Xavfsizlik uchun faqat shu userga tegishli xarajatni qidiramiz
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    
    if request.method == 'POST':
        category_id = request.POST.get('category')
        # Kategoriyani ham shu userga tegishli ekanini tekshirib olamiz
        category = get_object_or_404(Category, id=category_id, user=request.user)
        
        expense.category = category
        expense.amount = request.POST.get('amount')
        expense.description = request.POST.get('description')
        
        if request.POST.get('date'):
            expense.date = request.POST.get('date')
            
        expense.save() # O'zgarishlarni saqlaymiz
        return redirect('expense_list')
        
    categories = Category.objects.filter(user=request.user)
    return render(request, 'expenses/expense_form.html', {
        'expense': expense,
        'categories': categories
    })

@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)
    expense.delete()
    return redirect('expense_list')