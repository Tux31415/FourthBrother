import subprocess

# measured in seconds
DEFAULT_VIDEO_DURATION = 5 
MAXIMUM_VIDEO_DURATION = 30


def relay_command(bro, update, context):
    if bro.relay.value:
        bro.send_message("El relé se ha apagado")
        bro.relay.off()
    else:
        bro.send_message("El relé se ha encendido")
        bro.relay.on()
        
def photo_command(bro, update, context):
    if bro.using_camera.is_set():
        bro.send_message("La cámara no se encuentra disponible")
        return

    bro.using_camera.set()

    with bro.get_image_stream() as image_stream:
        bro.send_photo(image_stream)

    bro.using_camera.clear()

def video_command(bro, update, context):
    if bro.using_camera.is_set():
        bro.send_message("La cámara no se encuentra disponible")
        return
    
    bro.using_camera.set()

    duration = DEFAULT_VIDEO_DURATION
    if context.args:
        try:
            duration = int(context.args[0])
        except ValueError:
            bro.send_message("Por favor, introduce un número")
            bro.using_camera.clear()
            return

    if duration > MAXIMUM_VIDEO_DURATION:
        bro.send_message(f"No puedes hacer grabaciones de más de {MAXIMUM_VIDEO_DURATION} segundos")
        bro.using_camera.clear()
        return
    
    bro.record_and_send_video(duration)
    bro.using_camera.clear()

def movement_handler(bro):
    pass
