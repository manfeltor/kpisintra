from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import CustomUserCreationForm, CompanyForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .models import CustomUser, Company


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            error_message = 'Usuario y/o contraseña inválidos'
            return render(request, 'landing.html', {'login_error': error_message})  # Pass the error message
    return redirect('home')


@login_required
def create_user_view(request):
    if not request.user.is_superuser:
        return redirect('unauthorized')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_users')  # Redirect to home or another relevant page after creating the user
    else:
        form = CustomUserCreationForm()

    return render(request, 'create_user.html', {'form': form})


@login_required
def user_list_view(request):
    users = CustomUser.objects.all()  # Retrieve all users
    return render(request, 'list_users.html', {'users': users})


@staff_member_required  # Only allow staff/admins to delete users
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('list_users')

    return render(request, 'delete_user_confirmation.html', {'user': user})


@login_required
def companies_list_view(request):
    companies = Company.objects.all()  # Retrieve all users
    return render(request, 'list_companies.html', {'companies': companies})


@login_required
def modify_company_view(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    
    if not (request.user.is_management or request.user.is_superuser):
        return redirect('unauthorized')  # Redirect to unauthorized page if needed

    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, f"Compañia '{company.name}' modificada correctamente.")
            return redirect('list_companies')
    else:
        form = CompanyForm(instance=company)
    
    return render(request, 'modify_company.html', {'form': form, 'company': company})