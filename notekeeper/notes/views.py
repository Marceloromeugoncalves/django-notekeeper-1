from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Note, AddNoteForm
from django.contrib import messages
import json
from datetime import datetime, timedelta 
import os


def home(request):
    notes = Note.objects.filter(user=request.user).order_by('updated_at')
    form_error = False
    last_month = datetime.today() - timedelta(days=30)
    last_month_note_count = Note.objects.filter(
            user=request.user,
            created_at__gt=last_month
        ).count()
    
    if request.method == 'POST':
        form = AddNoteForm(request.POST)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.user = request.user
            form_data.save()
            # Without this next line the tags won't be saved.
            form.save_m2m()
            form = AddNoteForm()
            messages.success(request, 'Note added successfully!')
        else:
            form_error = True
    else:
        form = AddNoteForm()
    context = {
        'notes': notes,
        'add_note_form': form,
        'form_error': form_error,
        'last_month_note_count': last_month_note_count,
        'total_notes': len(notes),
    }
    return render(request, 'notes.html', context)

def get_note_details(request, slug):
    note = get_object_or_404(Note, slug=slug)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')

    notes = Note.objects.filter(user=request.user).order_by('updated_at')
    add_note_form = AddNoteForm()

    context = {
        'notes': notes,
        'note_detail': note,
        'add_note_form': add_note_form,
    }
    return render(request, 'note_details.html', context)

def edit_note_details(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    if request.method == 'POST':
        form = AddNoteForm(request.POST, instance=note)
        if form.is_valid():
            form_data = form.save(commit=False)
            form_data.user = request.user
            form_data.save()
            form.save_m2m()
            return redirect('note_detail', slug=note.slug)
    else:
        form = AddNoteForm(initial={
            'note_title': note.note_title,
            'note_content': note.note_content,
            'tags': ','.join([i.slug for i in note.tags.all()]),
        }, instance=note)
        return render(request, 'modals/edit_note_modal.html', {'form': form})

def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk)
    if note.user != request.user:
        messages.error(request, 'You are not authenticated to perform this action')
        return redirect('notes')
    note.delete()
    return redirect('notes')

def search_note(request):
    if request.is_ajax():
        q = request.GET.get('term')
        books = Book.objects.filter(
                book_name__icontains=q,
                added_by_user=request.user
            )[:10]
        results = []
        for book in books:
            book_json = {}
            book_json['slug'] = book.slug
            book_json['label'] = book.book_name
            book_json['value'] = book.book_name
            results.append(book_json)
        data = json.dumps(results)
    else:
        book_json = {}
        book_json['slug'] = None
        book_json['label'] = None
        book_json['value'] = None
        data = json.dumps(book_json)
    return HttpResponse(data)