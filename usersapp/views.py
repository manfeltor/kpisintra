from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required


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
            return redirect('home')  # Redirect to home or another relevant page after creating the user
    else:
        form = CustomUserCreationForm()

    return render(request, 'create_user.html', {'form': form})