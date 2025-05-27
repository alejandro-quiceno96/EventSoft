# app_asistente/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile
import io
import base64
from datetime import datetime
