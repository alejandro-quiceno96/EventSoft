
document.addEventListener("DOMContentLoaded", function () {
  // ... tu código existente ...

  // 👇 Agrega esto para cambiar entre secciones
  const btnUsuarios = document.getElementById("btnUsuarios");
  const btnAdmins = document.getElementById("btnAdmins");
  const usuariosSection = document.getElementById("usuariosSection");
  const adminsSection = document.getElementById("adminsSection");

  btnUsuarios.addEventListener("click", () => {
    usuariosSection.classList.remove("d-none");
    adminsSection.classList.add("d-none");
    btnUsuarios.classList.add("active");
    btnAdmins.classList.remove("active");
  });

  btnAdmins.addEventListener("click", () => {
    adminsSection.classList.remove("d-none");
    usuariosSection.classList.add("d-none");
    btnAdmins.classList.add("active");
    btnUsuarios.classList.remove("active");
  });
});
