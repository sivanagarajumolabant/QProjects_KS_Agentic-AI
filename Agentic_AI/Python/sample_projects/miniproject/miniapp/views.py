from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from .models import *
from .forms import *
from django.contrib.auth.decorators import login_required


# Create your views here.
@login_required
def create_emp(request):
    if request.method =='POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_emp')
    else:
        form = EmployeeForm()
    
    return render(request, 'create_emp.html', {'form': form})

@login_required
def emp_list(request):
    employees = Employee.objects.all()
    return render(request, 'emp_list.html', {'employees': employees})

@login_required
def update_emp(request, id):
    employee = get_object_or_404(Employee, id=id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('list_emp')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'create_emp.html', {'form': form})

@login_required
def delete_emp(request, id):
    employee  = Employee.objects.get(id=id)
    if request.method=='POST':
        employee.delete()
        return redirect('list_emp')
    return render(request, 'delete_emp.html', {'employee': employee})