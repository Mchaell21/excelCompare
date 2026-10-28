from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpRequest
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import update_session_auth_hash

from .decorators import superuser_required, login_required
from .forms import (
    LoginForm,
    UserCreateForm,
    UserPasswordForm,
    UserRoleForm,
    UserChangePasswordForm
)
from .service import user_service
from .otp_service import OTPTelegramService

from .utils.telegram import send_telegram

def login_view(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("")

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = user_service.login(
                request,
                form.cleaned_data["username"],
                form.cleaned_data["password"],
            )

            if user:
                return redirect("")
            messages.error(request, "Username atau password salah.")
        else:
            messages.error(request, "Silakan periksa kembali inputan Anda.")

    else:
        form = LoginForm(request)

    return render(request, "pages/auth/index.html", {"form": form})

def request_otp_login(request: HttpRequest):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        user = user_service.get_by_username(username)

        if not user:
            messages.error(request, "Username tidak ditemukan.")
            return redirect("users:login")

        if not user.chat_tele_id:
            messages.error(request, "Akun Anda belum terhubung ke Telegram. Silakan login menggunakan password.")
            return redirect("users:login")

        otp = OTPTelegramService.generate_otp(user.id)
        message = (
            f"🔑 <b>KODE OTP LOGIN</b>\n\n"
            f"Halo <b>{username}</b>, kode OTP login Sistem ---- Anda adalah:\n"
            f"<code>{otp}</code>\n\n"
            f"<i>Kode ini berlaku selama 5 menit. Jangan berikan kode ini kepada siapapun!</i>"
        )
        send_telegram(user.chat_tele_id, message=message)

        # Simpan state sementara di session
        request.session["pending_otp_user_id"] = str(user.id)
        
        messages.success(request, "Kode OTP telah dikirimkan ke akun Telegram Anda.")
        return redirect("users:login_otp")
    return redirect("users:login")

def login_otp_view(request: HttpRequest):
    """Halaman untuk menginput kode OTP."""
    user_id = request.session.get("pending_otp_user_id")
    if not user_id:
        messages.error(request, "Sesi OTP telah berakhir atau tidak valid.")
        return redirect("users:login")

    if request.method == "POST":
        otp_code = request.POST.get("otp_code", "").strip()
        success, msg = user_service.verify_and_login_otp(request, user_id, otp_code)

        if success:
            del request.session["pending_otp_user_id"]
            return redirect("")
        
        messages.error(request, msg)

    return render(request, "pages/auth/otp.html")

def logout_view(request: HttpRequest):
    user_service.logout(request)
    return redirect("users:login")


# ======================================================================
# Kelola User — khusus superadmin
# ======================================================================

def _target_user(request, user_id):
    """Ambil user target; superuser & diri sendiri tidak dikelola di sini."""
    user = user_service.get_user(user_id)
    if user is None:
        messages.error(request, "User tidak ditemukan.")
        return None
    if user.is_superuser:
        messages.error(request,
                       "Akun superuser tidak dikelola dari halaman ini.")
        return None
    if user.pk == request.user.pk:
        messages.error(request, "Tidak bisa mengubah akun Anda sendiri di sini.")
        return None
    return user


@superuser_required
@require_GET
def user_manage(request: HttpRequest):
    users = user_service.list_users()
    rows = []
    for u in users:
        role_names = [g.name for g in u.groups.all() if g.name != 'Superuser']
        rows.append({
            'user': u,
            'role_display': ', '.join(role_names) if role_names else
            ('Superuser' if u.is_superuser else '—'),
            'is_self': u.pk == request.user.pk,
            'editable': not u.is_superuser and u.pk != request.user.pk,
        })

    return render(request, "pages/users/manage.html", {
        "rows": rows,
        "role_form": UserRoleForm(),
        "active_roles": ["Sales Admin", "Dispatch", "Manager", "Accounting"],
    })


@superuser_required
def user_create(request: HttpRequest, user_id=None):
    user = None
    if user_id:
        user = user_service.get_user(user_id)
        if not user:
            messages.error(request, "User tidak ditemukan.")
            return redirect("users:manage")
        
    if request.method == "POST":
        form = UserCreateForm(request.POST, instance=user)
        if form.is_valid():
            saved_user = form.save()
            action_text = "diperbarui" if user_id else "dibuat"
            messages.success(
                request, f"User '{saved_user.username}' berhasil {action_text}."
            )

            role = form.cleaned_data.get("role")
            user_n = user_service.get_user(user_id) if user_id else saved_user
            if user_n and role:
                user_service.set_role(user=user_n, role=role)
            return redirect("users:manage")
    elif user:
        form = UserCreateForm(instance=user)
        if user_id and 'role' in form.fields:
            del form.fields['role']
    else:
        form = UserCreateForm()

    return render(request, "pages/users/create.html", {
        "form": form, 
        "is_edit": bool(user_id),
        "user_obj": user,
    })


@superuser_required
@require_POST
def user_toggle_active(request: HttpRequest, user_id):
    user = _target_user(request, user_id)
    if user is None:
        return redirect("users:manage")

    user_service.set_active(user, not user.is_active)
    state = "diaktifkan" if user.is_active else "dinonaktifkan"
    messages.success(request, f"User '{user.username}' {state}.")
    return redirect("users:manage")


@superuser_required
@require_POST
def user_change_role(request: HttpRequest, user_id):
    user = _target_user(request, user_id)
    if user is None:
        return redirect("users:manage")

    form = UserRoleForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Pilihan role tidak valid.")
        return redirect("users:manage")

    role = form.cleaned_data.get("role")
    user_service.set_role(user, role)
    messages.success(
        request,
        f"Role '{user.username}' diubah menjadi "
        f"{role or 'tanpa role'}.")
    return redirect("users:manage")


@superuser_required
def user_reset_password(request: HttpRequest, user_id):
    user = _target_user(request, user_id)
    if user is None:
        return redirect("users:manage")

    if request.method == "POST":
        form = UserPasswordForm(request.POST)
        if form.is_valid():
            user_service.reset_password(user, form.cleaned_data["new_password"])
            messages.success(
                request, f"Password '{user.username}' berhasil di-reset.")
            return redirect("users:manage")
    else:
        form = UserPasswordForm()

    return render(request, "pages/users/reset_password.html", {
        "form": form,
        "target_user": user,
    })

@login_required
def user_profile(request: HttpRequest):
    password_form = UserChangePasswordForm(user=request.user)
    return render(request, "pages/users/profile.html", {
        "user_obj": request.user,
        "password_form": password_form,
    })

@login_required
@require_POST
def change_password(request: HttpRequest):
    form = UserChangePasswordForm(user=request.user, data=request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Kata sandi berhasil diperbarui.")
        return redirect("users:profile")
    
    return render(request, "pages/users/profile.html", {
        "user_obj": request.user,
        "password_form": form,
    })

@login_required
@require_POST
def telegram_confirm(request: HttpRequest):
    action = request.POST.get("action")
    if action == "confirm":
        success, msg = user_service.confirm_telegram(request.user)
        if success:
            messages.success(request, msg)
        else:
            messages.error(request, msg)
    elif action == "reject":
        user_service.reject_telegram(request.user)
        messages.info(request, "Permintaan penghubungan Telegram ditolak.")
        
    return redirect("users:profile")

@login_required
@require_POST
def telegram_disconnect(request: HttpRequest):
    user_service.disconnect_telegram(request.user)
    messages.success(request, "Koneksi Telegram berhasil diputuskan.")
    return redirect("users:profile")