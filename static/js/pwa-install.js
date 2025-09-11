// static/js/pwa-install.js
// Manejo de instalación de PWA para PublicTrack

let deferredPrompt;
let installButton = null;

window.addEventListener('DOMContentLoaded', () => {
    // Buscar o crear el botón de instalación
    installButton = document.getElementById('install-pwa-btn');
    
    // Si no existe el botón, crearlo dinámicamente
    if (!installButton) {
        createInstallButton();
    }
});

// Capturar el evento beforeinstallprompt
window.addEventListener('beforeinstallprompt', (e) => {
    console.log('Evento beforeinstallprompt capturado');
    
    // Prevenir que Chrome muestre el mini-infobar
    e.preventDefault();
    
    // Guardar el evento para usarlo después
    deferredPrompt = e;
    
    // Mostrar el botón de instalación
    showInstallButton();
    
    // Mostrar notificación toast
    showInstallNotification();
});

// Función para crear el botón de instalación
function createInstallButton() {
    // Crear contenedor flotante
    const buttonContainer = document.createElement('div');
    buttonContainer.id = 'pwa-install-container';
    buttonContainer.innerHTML = `
        <button id="install-pwa-btn" class="btn btn-primary shadow-lg" style="display: none;">
            <i class="fas fa-download me-2"></i>
            Instalar App
        </button>
    `;
    buttonContainer.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
    `;
    
    document.body.appendChild(buttonContainer);
    installButton = document.getElementById('install-pwa-btn');
    
    // Agregar evento click al botón
    installButton.addEventListener('click', installPWA);
}

// Función para mostrar el botón
function showInstallButton() {
    if (installButton) {
        installButton.style.display = 'inline-block';
        
        // Animar la entrada del botón
        installButton.style.animation = 'slideInUp 0.5s ease-out';
    }
}

// Función para ocultar el botón
function hideInstallButton() {
    if (installButton) {
        installButton.style.animation = 'slideOutDown 0.5s ease-out';
        setTimeout(() => {
            installButton.style.display = 'none';
        }, 500);
    }
}

// Función para instalar la PWA
async function installPWA() {
    if (!deferredPrompt) {
        console.log('No hay prompt de instalación disponible');
        return;
    }
    
    // Mostrar el prompt de instalación
    deferredPrompt.prompt();
    
    // Esperar a que el usuario responda
    const { outcome } = await deferredPrompt.userChoice;
    
    console.log(`Usuario respondió: ${outcome}`);
    
    if (outcome === 'accepted') {
        console.log('Usuario aceptó instalar la PWA');
        showSuccessMessage();
    } else {
        console.log('Usuario rechazó instalar la PWA');
    }
    
    // Limpiar el prompt
    deferredPrompt = null;
    
    // Ocultar el botón
    hideInstallButton();
}

// Mostrar notificación de que se puede instalar
function showInstallNotification() {
    // Crear notificación toast
    const toast = document.createElement('div');
    toast.className = 'toast show position-fixed top-0 end-0 m-3';
    toast.style.zIndex = '10000';
    toast.innerHTML = `
        <div class="toast-header bg-primary text-white">
            <i class="fas fa-mobile-alt me-2"></i>
            <strong class="me-auto">¡Instala PublicTrack!</strong>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            Puedes instalar PublicTrack como una aplicación en tu dispositivo para acceso rápido.
            <div class="mt-2">
                <button class="btn btn-sm btn-primary" onclick="installPWA()">
                    Instalar Ahora
                </button>
                <button class="btn btn-sm btn-secondary" data-bs-dismiss="toast">
                    Más Tarde
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-ocultar después de 10 segundos
    setTimeout(() => {
        toast.remove();
    }, 10000);
}

// Mostrar mensaje de éxito
function showSuccessMessage() {
    const alert = document.createElement('div');
    alert.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alert.style.zIndex = '10001';
    alert.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        ¡PublicTrack se ha instalado correctamente!
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(alert);
    
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// Detectar si ya está instalada
window.addEventListener('appinstalled', () => {
    console.log('PWA instalada');
    hideInstallButton();
});

// Verificar si está en modo standalone
if (window.matchMedia('(display-mode: standalone)').matches) {
    console.log('La app está ejecutándose en modo standalone');
}

// Agregar estilos de animación
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInUp {
        from {
            transform: translateY(100%);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutDown {
        from {
            transform: translateY(0);
            opacity: 1;
        }
        to {
            transform: translateY(100%);
            opacity: 0;
        }
    }
    
    #install-pwa-btn {
        transition: transform 0.3s ease;
    }
    
    #install-pwa-btn:hover {
        transform: scale(1.05);
    }
`;
document.head.appendChild(style);

// Función para verificar manualmente si se puede instalar
function checkInstallability() {
    // Esta función es útil para debugging
    console.log('Verificando instalabilidad...');
    console.log('HTTPS:', window.location.protocol === 'https:' || window.location.hostname === 'localhost');
    console.log('Service Worker:', 'serviceWorker' in navigator);
    console.log('Manifest presente:', document.querySelector('link[rel="manifest"]') !== null);
    
    // Forzar mostrar el botón para pruebas (solo en desarrollo)
    if (window.location.hostname === 'localhost') {
        setTimeout(() => {
            if (!deferredPrompt && installButton) {
                console.log('Mostrando botón de instalación manual para pruebas');
                showInstallButton();
                
                // Simular instalación para desarrollo
                installButton.onclick = () => {
                    alert('En un entorno de producción con HTTPS, aquí aparecería el diálogo de instalación.\n\nRequisitos para instalación:\n1. HTTPS (o localhost)\n2. Manifest válido\n3. Service Worker registrado\n4. Iconos 192x192 y 512x512');
                };
            }
        }, 2000);
    }
}

// Ejecutar verificación cuando cargue la página
window.addEventListener('load', checkInstallability);

// Exportar funciones para uso global
window.installPWA = installPWA;
window.showInstallButton = showInstallButton;
window.hideInstallButton = hideInstallButton;