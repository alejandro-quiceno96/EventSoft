document.addEventListener("DOMContentLoaded", function () {
  const grupoDiseno = document.getElementById("grupo-diseno");
  const grupoFirma = document.getElementById("grupo-firma");

  const conDiseno = document.getElementById("con_diseno");
  const conFirma = document.getElementById("con_firma");

  const preview = document.getElementById("preview-certificado");
  const textoCert = document.getElementById("preview-texto");

  const firmaImg = document.getElementById("preview-firma");
  const nombreFirmante = document.getElementById("preview-nombre");
  const cargoFirmante = document.getElementById("preview-cargo");

const constar = document.getElementById("constar");

  const nombreGeneraCertificado = document.getElementById("nombre_genera_certificado");

  // Mostrar/ocultar diseño
  conDiseno.addEventListener("change", () => {
    grupoDiseno.style.display = conDiseno.value === "si" ? "block" : "none";
  });

  // Mostrar/ocultar firma
  conFirma.addEventListener("change", () => {
    grupoFirma.style.display = conFirma.value === "si" ? "block" : "none";
  });

  // Previsualizar certificado
  document.getElementById("btn-previsualizar").addEventListener("click", () => {
    // Mostrar modal
    document.getElementById("modal-preview").style.display = "block";
    // Nombre del certificador
    const nombreCertificador = document.getElementById("id_nombre_certificador").value;
    nombreGeneraCertificado.textContent = `${nombreCertificador.toUpperCase()}`;
    // Aplicar tipografía
    const tipografia = document.getElementById("tipografia").value;
    textoCert.style.fontFamily = tipografia;
    nombreGeneraCertificado.style.fontFamily = tipografia;
    constar.style.fontFamily = tipografia;
    document.getElementById("preview-lugar-fecha").style.fontFamily = tipografia;
    nombreFirmante.style.fontFamily = tipografia;
    cargoFirmante.style.fontFamily = tipografia;
    constar.style.fontWeight = "bold";
    // Orientación
    const orientacion = document.getElementById("orientacion").value;
    if (orientacion === "vertical") {
      preview.style.width = "816px";
      preview.style.height = "1056px";
    } else {
      preview.style.width = "1056px";
      preview.style.height = "816px";
    }

    // Fondo diseño
    const inputDiseno = document.getElementById("id_diseno");
    if (inputDiseno.files.length > 0) {
      const reader = new FileReader();
        reader.onload = (e) => {
          preview.style.backgroundImage = `url('${e.target.result}')`;
        };
      
      reader.readAsDataURL(inputDiseno.files[0]);
    } else {
        if (orientacion === "vertical") {
          preview.style.backgroundImage = "url('../../../../static/image/certificado_vertical.png')";
          document.getElementById("preview-lugar-fecha").style.right = "120px";
        } else {
            preview.style.backgroundImage = "url('../../../../static/image/')"; 
        }
      
    }

    // Agrega al final de la función del click de previsualización

    const lugar = document.getElementById("lugar_expedicion").value;
    const fechaHoy = new Date();
    const opcionesFecha = { year: 'numeric', month: 'long', day: 'numeric' };
    const fechaFormateada = fechaHoy.toLocaleDateString('es-ES', opcionesFecha);

    document.getElementById(
      "preview-lugar-fecha"
    ).textContent = `Para constancia se expedide en ${lugar}, el día ${fechaFormateada}.`;


    // Firma
    const firmaInput = document.getElementById("id_firma");
    if (firmaInput.files.length > 0) {
      const reader = new FileReader();
      reader.onload = e => {
        firmaImg.src = e.target.result;
        firmaImg.style.display = "block";
        nombreFirmante.style.borderTop = "1px solid black";
      };
      reader.readAsDataURL(firmaInput.files[0]);
    } else {
      firmaImg.style.display = "none";
    }

    // Nombre y cargo
    nombreFirmante.textContent = document.getElementById("id_firma_nombre").value;
    cargoFirmante.textContent = document.getElementById("id_firma_cargo").value;
  });
});
