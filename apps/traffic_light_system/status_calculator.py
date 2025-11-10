"""
Calculadora de Estados del Sistema de Semáforos
Sistema PubliTrack - Lógica core para determinar estados de cuñas
"""

from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)

class StatusCalculator:
    """
    Calculadora principal para determinar estados de semáforos
    """
    
    def __init__(self, configuracion=None):
        """
        Inicializa la calculadora con una configuración específica
        """
        if configuracion is None:
            from .models import ConfiguracionSemaforo
            configuracion = ConfiguracionSemaforo.get_active()
        
        self.configuracion = configuracion
        self.hoy = timezone.now().date()
    
    def calcular_estado_cuña(self, cuña) -> Dict[str, Any]:
        """
        Calcula el estado del semáforo para una cuña específica
        
        Args:
            cuña: Instancia de CuñaPublicitaria
            
        Returns:
            Dict con el estado calculado
        """
        try:
            # Preparar datos base
            resultado = {
                'color': 'gris',
                'prioridad': 'baja',
                'razon': 'Estado no determinado',
                'dias_restantes': None,
                'porcentaje_tiempo': None,
                'metadatos': {},
                'requiere_alerta': False
            }
            
            # Validar que la cuña tenga fechas
            if not cuña.fecha_inicio or not cuña.fecha_fin:
                resultado.update({
                    'color': 'gris',
                    'razon': 'Cuña sin fechas definidas',
                    'metadatos': {'error': 'Fechas faltantes'}
                })
                return resultado
            
            # Calcular métricas temporales
            dias_restantes = self._calcular_dias_restantes(cuña)
            porcentaje_tiempo = self._calcular_porcentaje_tiempo_transcurrido(cuña)
            
            resultado['dias_restantes'] = dias_restantes
            resultado['porcentaje_tiempo'] = porcentaje_tiempo
            
            # Determinar color según tipo de cálculo
            if self.configuracion.tipo_calculo == 'estado_cuña':
                color, razon = self._calcular_por_estado(cuña)
            elif self.configuracion.tipo_calculo == 'dias_restantes':
                color, razon = self._calcular_por_dias_restantes(cuña, dias_restantes)
            elif self.configuracion.tipo_calculo == 'porcentaje_tiempo':
                color, razon = self._calcular_por_porcentaje_tiempo(cuña, porcentaje_tiempo)
            else:  # combinado
                color, razon = self._calcular_combinado(cuña, dias_restantes, porcentaje_tiempo)
            
            # Determinar prioridad
            prioridad = self._determinar_prioridad(color, cuña, dias_restantes, porcentaje_tiempo)
            
            # Verificar si requiere alerta
            requiere_alerta = self._requiere_alerta(color, cuña, dias_restantes)
            
            resultado.update({
                'color': color,
                'prioridad': prioridad,
                'razon': razon,
                'requiere_alerta': requiere_alerta,
                'metadatos': {
                    'tipo_calculo': self.configuracion.tipo_calculo,
                    'configuracion_id': self.configuracion.id,
                    'calculado_en': timezone.now().isoformat(),
                    'estado_cuña': cuña.estado,
                    'fecha_calculo': self.hoy.isoformat()
                }
            })
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error calculando estado para cuña {cuña.codigo}: {str(e)}")
            return {
                'color': 'gris',
                'prioridad': 'baja',
                'razon': f'Error en cálculo: {str(e)}',
                'dias_restantes': None,
                'porcentaje_tiempo': None,
                'metadatos': {'error': str(e)},
                'requiere_alerta': False
            }
    
    def _calcular_dias_restantes(self, cuña) -> Optional[int]:
        """Calcula los días restantes hasta el fin de la campaña"""
        if not cuña.fecha_fin:
            return None
        
        return (cuña.fecha_fin - self.hoy).days
    
    def _calcular_porcentaje_tiempo_transcurrido(self, cuña) -> Optional[Decimal]:
        """Calcula el porcentaje de tiempo transcurrido de la campaña"""
        if not cuña.fecha_inicio or not cuña.fecha_fin:
            return None
        
        try:
            duracion_total = (cuña.fecha_fin - cuña.fecha_inicio).days
            if duracion_total <= 0:
                return Decimal('100.00')
            
            if self.hoy < cuña.fecha_inicio:
                return Decimal('0.00')
            elif self.hoy > cuña.fecha_fin:
                return Decimal('100.00')
            else:
                dias_transcurridos = (self.hoy - cuña.fecha_inicio).days
                porcentaje = (dias_transcurridos / duracion_total) * 100
                return Decimal(str(round(porcentaje, 2)))
        except Exception:
            return None
    # En apps/traffic_light_system/utils/status_calculator.py

def _calcular_por_estado(self, cuña) -> Tuple[str, str]:
    """Calcula color basado únicamente en el estado de la cuña"""
    estado = cuña.estado
    
    # Estados que siempre muestran verde (activos)
    if estado in ['activa', 'aprobada']:
        # Verificar si está en fecha válida
        if cuña.fecha_inicio and cuña.fecha_fin:
            hoy = timezone.now().date()
            if cuña.fecha_inicio <= hoy <= cuña.fecha_fin:
                return 'verde', f'Estado "{estado}" y dentro del periodo activo'
            elif hoy < cuña.fecha_inicio:
                return 'amarillo', f'Estado "{estado}" pero campaña no ha iniciado'
            else:
                return 'rojo', f'Estado "{estado}" pero campaña ha finalizado'
        return 'verde', f'Estado "{estado}" - Sin verificación de fechas'
    
    # Estados que muestran amarillo (en proceso)
    elif estado in ['pendiente_revision', 'en_produccion', 'pausada']:
        return 'amarillo', f'Estado "{estado}" - Requiere atención'
    
    # Estados que muestran rojo (problemas)
    elif estado in ['borrador', 'cancelada']:
        return 'rojo', f'Estado "{estado}" - Acción requerida'
    
    # Estados que muestran gris (finalizados)
    elif estado in ['finalizada']:
        return 'gris', f'Estado "{estado}" - Finalizada'
    
    # Estado por defecto
    else:
        return 'amarillo', f'Estado "{estado}" no clasificado, por defecto amarillo'
    def _calcular_por_dias_restantes(self, cuña, dias_restantes) -> Tuple[str, str]:
        """Calcula color basado en días restantes"""
        if dias_restantes is None:
            return 'gris', 'No se pueden calcular días restantes'
        
        if dias_restantes < 0:
            return 'rojo', f'Cuña vencida hace {abs(dias_restantes)} días'
        elif dias_restantes < self.configuracion.dias_amarillo_min:
            return 'rojo', f'Quedan {dias_restantes} días (crítico)'
        elif dias_restantes < self.configuracion.dias_verde_min:
            return 'amarillo', f'Quedan {dias_restantes} días (precaución)'
        else:
            return 'verde', f'Quedan {dias_restantes} días (normal)'
    
    def _calcular_por_porcentaje_tiempo(self, cuña, porcentaje_tiempo) -> Tuple[str, str]:
        """Calcula color basado en porcentaje de tiempo transcurrido"""
        if porcentaje_tiempo is None:
            return 'gris', 'No se puede calcular porcentaje de tiempo'
        
        if porcentaje_tiempo >= 100:
            return 'rojo', 'Campaña finalizada (100% del tiempo transcurrido)'
        elif porcentaje_tiempo > self.configuracion.porcentaje_amarillo_max:
            return 'rojo', f'{porcentaje_tiempo}% del tiempo transcurrido (crítico)'
        elif porcentaje_tiempo > self.configuracion.porcentaje_verde_max:
            return 'amarillo', f'{porcentaje_tiempo}% del tiempo transcurrido (precaución)'
        else:
            return 'verde', f'{porcentaje_tiempo}% del tiempo transcurrido (normal)'
    
    def _calcular_combinado(self, cuña, dias_restantes, porcentaje_tiempo) -> Tuple[str, str]:
        """Calcula color usando método combinado (estado + tiempo)"""
        # Primero verificar el estado
        color_estado, razon_estado = self._calcular_por_estado(cuña)
        
        # Si el estado indica gris (finalizada/cancelada), mantener gris
        if color_estado == 'gris':
            return color_estado, razon_estado
        
        # Si el estado es rojo, mantener rojo independientemente del tiempo
        if color_estado == 'rojo':
            return color_estado, razon_estado
        
        # Para estados verde/amarillo, verificar métricas de tiempo
        color_dias, razon_dias = self._calcular_por_dias_restantes(cuña, dias_restantes)
        color_porcentaje, razon_porcentaje = self._calcular_por_porcentaje_tiempo(cuña, porcentaje_tiempo)
        
        # Tomar el color más crítico entre tiempo y estado
        colores_orden = {'verde': 1, 'amarillo': 2, 'rojo': 3, 'gris': 0}
        
        color_final = max([color_estado, color_dias, color_porcentaje], 
                         key=lambda x: colores_orden.get(x, 0))
        
        # Construir razón combinada
        razones = []
        if color_estado != 'verde':
            razones.append(razon_estado)
        if color_dias != 'verde':
            razones.append(razon_dias)
        if color_porcentaje != 'verde':
            razones.append(razon_porcentaje)
        
        if razones:
            razon_final = ' | '.join(razones)
        else:
            razon_final = 'Estado y tiempo dentro de parámetros normales'
        
        return color_final, razon_final
    
    def _determinar_prioridad(self, color, cuña, dias_restantes, porcentaje_tiempo) -> str:
        """Determina la prioridad basada en el color y otros factores"""
        if color == 'rojo':
            # Crítica si está vencida o muy próxima a vencer
            if dias_restantes is not None and dias_restantes < 0:
                return 'critica'
            elif dias_restantes is not None and dias_restantes <= 3:
                return 'critica'
            else:
                return 'alta'
        elif color == 'amarillo':
            # Alta si quedan pocos días, media en otros casos
            if dias_restantes is not None and dias_restantes <= 7:
                return 'alta'
            else:
                return 'media'
        elif color == 'verde':
            return 'baja'
        else:  # gris
            return 'baja'
    
    def _requiere_alerta(self, color, cuña, dias_restantes) -> bool:
        """Determina si el estado requiere generar una alerta"""
        if not self.configuracion.enviar_alertas:
            return False
        
        # Alertar para estados críticos
        if color == 'rojo':
            return True
        
        # Alertar para amarillo si está muy próximo a vencer
        if color == 'amarillo' and dias_restantes is not None and dias_restantes <= 3:
            return True
        
        # Alertar si la cuña requiere revisión y está activa
        if cuña.estado in ['pendiente_revision'] and color in ['amarillo', 'rojo']:
            return True
        
        return False
    
    def actualizar_estado_cuña(self, cuña, crear_historial=True) -> 'EstadoSemaforo':
        """
        Actualiza o crea el estado de semáforo para una cuña
        
        Args:
            cuña: Instancia de CuñaPublicitaria
            crear_historial: Si crear entrada en el historial
            
        Returns:
            Instancia de EstadoSemaforo actualizada
        """
        from .models import EstadoSemaforo, HistorialEstadoSemaforo
        
        # Calcular nuevo estado
        nuevo_estado = self.calcular_estado_cuña(cuña)
        
        with transaction.atomic():
            # Obtener o crear estado actual
            estado_semaforo, created = EstadoSemaforo.objects.get_or_create(
                cuña=cuña,
                defaults={
                    'color_actual': nuevo_estado['color'],
                    'prioridad': nuevo_estado['prioridad'],
                    'razon_color': nuevo_estado['razon'],
                    'dias_restantes': nuevo_estado['dias_restantes'],
                    'porcentaje_tiempo_transcurrido': nuevo_estado['porcentaje_tiempo'],
                    'metadatos_calculo': nuevo_estado['metadatos'],
                    'requiere_alerta': nuevo_estado['requiere_alerta'],
                    'configuracion_utilizada': self.configuracion
                }
            )
            
            # Si ya existía, verificar cambios
            if not created:
                color_anterior = estado_semaforo.color_actual
                
                # Actualizar valores
                estado_semaforo.color_anterior = color_anterior
                estado_semaforo.color_actual = nuevo_estado['color']
                estado_semaforo.prioridad = nuevo_estado['prioridad']
                estado_semaforo.razon_color = nuevo_estado['razon']
                estado_semaforo.dias_restantes = nuevo_estado['dias_restantes']
                estado_semaforo.porcentaje_tiempo_transcurrido = nuevo_estado['porcentaje_tiempo']
                estado_semaforo.metadatos_calculo = nuevo_estado['metadatos']
                estado_semaforo.requiere_alerta = nuevo_estado['requiere_alerta']
                estado_semaforo.configuracion_utilizada = self.configuracion
                estado_semaforo.alerta_enviada = False  # Reset para nueva evaluación
                estado_semaforo.save()
                
                # Crear historial si hubo cambio de color
                if crear_historial and color_anterior != nuevo_estado['color']:
                    HistorialEstadoSemaforo.objects.create(
                        cuña=cuña,
                        color_anterior=color_anterior,
                        color_nuevo=nuevo_estado['color'],
                        prioridad_anterior=estado_semaforo.prioridad,
                        prioridad_nueva=nuevo_estado['prioridad'],
                        razon_cambio=nuevo_estado['razon'],
                        dias_restantes=nuevo_estado['dias_restantes'],
                        porcentaje_tiempo=nuevo_estado['porcentaje_tiempo'],
                        configuracion_utilizada=self.configuracion,
                        alerta_generada=nuevo_estado['requiere_alerta']
                    )
            else:
                # Nueva cuña - crear historial inicial
                if crear_historial:
                    HistorialEstadoSemaforo.objects.create(
                        cuña=cuña,
                        color_anterior=None,
                        color_nuevo=nuevo_estado['color'],
                        prioridad_anterior=None,
                        prioridad_nueva=nuevo_estado['prioridad'],
                        razon_cambio=f"Estado inicial: {nuevo_estado['razon']}",
                        dias_restantes=nuevo_estado['dias_restantes'],
                        porcentaje_tiempo=nuevo_estado['porcentaje_tiempo'],
                        configuracion_utilizada=self.configuracion,
                        alerta_generada=nuevo_estado['requiere_alerta']
                    )
        
        return estado_semaforo
    
    def actualizar_todas_las_cuñas(self, filtros=None) -> Dict[str, int]:
        """
        Actualiza estados para todas las cuñas (o las filtradas)
        
        Args:
            filtros: Filtros Q para aplicar a las cuñas
            
        Returns:
            Dict con estadísticas del proceso
        """
        from apps.content_management.models import CuñaPublicitaria
        
        logger.info("Iniciando actualización masiva de estados de semáforo")
        
        # Obtener cuñas a procesar
        cuñas_query = CuñaPublicitaria.objects.select_related('categoria', 'tipo_contrato')
        
        if filtros:
            cuñas_query = cuñas_query.filter(filtros)
        
        cuñas = cuñas_query.all()
        
        # Contadores
        stats = {
            'total_procesadas': 0,
            'actualizadas': 0,
            'creadas': 0,
            'errores': 0,
            'cambios_color': 0,
            'alertas_generadas': 0
        }
        
        for cuña in cuñas:
            try:
                # Verificar si había estado anterior
                estado_anterior = getattr(cuña, 'estado_semaforo', None)
                color_anterior = estado_anterior.color_actual if estado_anterior else None
                
                # Actualizar estado
                estado_actualizado = self.actualizar_estado_cuña(cuña)
                
                stats['total_procesadas'] += 1
                
                if color_anterior is None:
                    stats['creadas'] += 1
                else:
                    stats['actualizadas'] += 1
                    
                    if color_anterior != estado_actualizado.color_actual:
                        stats['cambios_color'] += 1
                
                if estado_actualizado.requiere_alerta:
                    stats['alertas_generadas'] += 1
                
            except Exception as e:
                logger.error(f"Error procesando cuña {cuña.codigo}: {str(e)}")
                stats['errores'] += 1
        
        logger.info(f"Actualización completada: {stats}")
        return stats
    
    def obtener_estadisticas_resumen(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas resumidas del estado actual
        """
        from .models import EstadoSemaforo
        from django.db.models import Count, Q
        
        # Contadores básicos
        stats = EstadoSemaforo.objects.aggregate(
            total=Count('id'),
            verde=Count('id', filter=Q(color_actual='verde')),
            amarillo=Count('id', filter=Q(color_actual='amarillo')),
            rojo=Count('id', filter=Q(color_actual='rojo')),
            gris=Count('id', filter=Q(color_actual='gris')),
            con_alertas=Count('id', filter=Q(requiere_alerta=True)),
            alertas_pendientes=Count('id', filter=Q(requiere_alerta=True, alerta_enviada=False))
        )
        
        # Calcular porcentajes
        total = stats['total'] or 1  # Evitar división por cero
        
        return {
            'total_cuñas': stats['total'],
            'contadores': {
                'verde': stats['verde'],
                'amarillo': stats['amarillo'],
                'rojo': stats['rojo'],
                'gris': stats['gris']
            },
            'porcentajes': {
                'verde': round((stats['verde'] / total) * 100, 2),
                'amarillo': round((stats['amarillo'] / total) * 100, 2),
                'rojo': round((stats['rojo'] / total) * 100, 2),
                'gris': round((stats['gris'] / total) * 100, 2),
                'problemas': round(((stats['amarillo'] + stats['rojo']) / total) * 100, 2)
            },
            'alertas': {
                'total_con_alertas': stats['con_alertas'],
                'alertas_pendientes': stats['alertas_pendientes']
            },
            'configuracion_activa': self.configuracion.nombre,
            'fecha_calculo': timezone.now()
        }


class AlertasManager:
    """
    Gestor de alertas del sistema de semáforos
    """
    
    def __init__(self):
        from .models import ConfiguracionSemaforo
        self.configuracion = ConfiguracionSemaforo.get_active()
    
    def generar_alertas_pendientes(self) -> Dict[str, int]:
        """
        Genera alertas para estados que las requieren
        """
        from .models import EstadoSemaforo, AlertaSemaforo
        from django.db.models import Q
        
        stats = {
            'alertas_creadas': 0,
            'errores': 0
        }
        
        # Obtener estados que requieren alerta pero no la tienen enviada
        estados_pendientes = EstadoSemaforo.objects.filter(
            requiere_alerta=True,
            alerta_enviada=False
        ).select_related('cuña')
        
        for estado in estados_pendientes:
            try:
                # Verificar si ya existe alerta reciente para esta cuña
                alerta_existente = AlertaSemaforo.objects.filter(
                    cuña=estado.cuña,
                    estado='pendiente',
                    created_at__gte=timezone.now() - timedelta(hours=24)
                ).exists()
                
                if not alerta_existente:
                    self._crear_alerta_para_estado(estado)
                    stats['alertas_creadas'] += 1
                
            except Exception as e:
                logger.error(f"Error creando alerta para cuña {estado.cuña.codigo}: {str(e)}")
                stats['errores'] += 1
        
        return stats
    
    def _crear_alerta_para_estado(self, estado_semaforo):
        """Crea una alerta específica para un estado de semáforo"""
        from .models import AlertaSemaforo
        
        cuña = estado_semaforo.cuña
        color = estado_semaforo.color_actual
        
        # Determinar tipo y severidad
        if color == 'rojo':
            tipo_alerta = 'estado_critico'
            severidad = 'critical' if estado_semaforo.dias_restantes and estado_semaforo.dias_restantes < 0 else 'error'
            titulo = f"Estado Crítico: {cuña.codigo}"
        elif color == 'amarillo':
            tipo_alerta = 'vencimiento_proximo'
            severidad = 'warning'
            titulo = f"Vencimiento Próximo: {cuña.codigo}"
        else:
            tipo_alerta = 'cambio_estado'
            severidad = 'info'
            titulo = f"Cambio de Estado: {cuña.codigo}"
        
        # Construir mensaje
        mensaje = self._construir_mensaje_alerta(estado_semaforo)
        
        # Determinar destinatarios
        usuarios_destino = self._obtener_usuarios_destino(cuña)
        
        # Crear alerta
        alerta = AlertaSemaforo.objects.create(
            cuña=cuña,
            estado_semaforo=estado_semaforo,
            tipo_alerta=tipo_alerta,
            severidad=severidad,
            titulo=titulo,
            mensaje=mensaje,
            roles_destino=['admin', 'vendedor'],
            enviar_email=True,
            enviar_push=True,
            mostrar_dashboard=True
        )
        
        # Agregar usuarios específicos
        if usuarios_destino:
            alerta.usuarios_destino.set(usuarios_destino)
        
        return alerta
    
    def _construir_mensaje_alerta(self, estado_semaforo) -> str:
        """Construye el mensaje detallado de la alerta"""
        cuña = estado_semaforo.cuña
        
        mensaje_partes = [
            f"Cuña: {cuña.titulo}",
            f"Cliente: {cuña.cliente.get_full_name()}",
            f"Estado: {estado_semaforo.get_color_actual_display()}",
            f"Razón: {estado_semaforo.razon_color}"
        ]
        
        if estado_semaforo.dias_restantes is not None:
            if estado_semaforo.dias_restantes < 0:
                mensaje_partes.append(f"⚠️ VENCIDA hace {abs(estado_semaforo.dias_restantes)} días")
            else:
                mensaje_partes.append(f"📅 Vence en {estado_semaforo.dias_restantes} días")
        
        if cuña.vendedor_asignado:
            mensaje_partes.append(f"Vendedor: {cuña.vendedor_asignado.get_full_name()}")
        
        # Agregar acciones recomendadas
        if estado_semaforo.color_actual == 'rojo':
            mensaje_partes.append("\n🔴 ACCIONES REQUERIDAS:")
            mensaje_partes.append("- Contactar al cliente inmediatamente")
            mensaje_partes.append("- Verificar renovación o finalización")
            mensaje_partes.append("- Actualizar estado de la cuña")
        elif estado_semaforo.color_actual == 'amarillo':
            mensaje_partes.append("\n🟡 ACCIONES RECOMENDADAS:")
            mensaje_partes.append("- Contactar al cliente para renovación")
            mensaje_partes.append("- Preparar documentación de cierre")
        
        return "\n".join(mensaje_partes)
    
    def _obtener_usuarios_destino(self, cuña) -> List:
        """Obtiene la lista de usuarios que deben recibir la alerta"""
        from apps.authentication.models import CustomUser
        
        usuarios = []
        
        # Agregar vendedor asignado
        if cuña.vendedor_asignado:
            usuarios.append(cuña.vendedor_asignado)
        
        # Agregar supervisor del vendedor
        if cuña.vendedor_asignado and cuña.vendedor_asignado.supervisor:
            usuarios.append(cuña.vendedor_asignado.supervisor)
        
        # Agregar administradores
        admins = CustomUser.objects.filter(
            rol='admin',
            is_active=True,
            status='activo'
        )
        usuarios.extend(admins)
        
        return list(set(usuarios))  # Eliminar duplicados


def recalcular_estados_masivo():
    """
    Función utilitaria para recalcular todos los estados
    """
    calculator = StatusCalculator()
    return calculator.actualizar_todas_las_cuñas()


def generar_alertas_pendientes():
    """
    Función utilitaria para generar alertas pendientes
    """
    manager = AlertasManager()
    return manager.generar_alertas_pendientes()