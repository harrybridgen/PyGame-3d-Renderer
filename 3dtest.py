import pygame
import math

pygame.init()

screen_width = 1600
screen_height = screen_width // 16 * 9

screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("3D Test")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
pygame.font.init() 

debug = False
draw_faces = False

WHITE = (255, 255, 255)
RED = (255, 0, 0)

ground_square_color = (10, 180, 10) 
ground_square_outline_color = (20, 150, 20)  

block_points = []
block_edges = []
render_distance = 4000 
face_size = 200

occupied_positions = set()
player_height = 500
camera_pos = [0, player_height, 0]  
yaw, pitch = 0, 0 
fov = 70
near_clip = 100
far_clip = render_distance
camera_lerp_factor = 0.5
target_yaw, target_pitch = yaw, pitch
target_pos = list(camera_pos)
player_movement_speed = 1200
player_movement_smooth = 0.5
camera_speed = 0.001
strafe_speed = player_movement_speed * 0.8
fov_rad = 1 / math.tan(math.radians(fov) / 2)

font_size = 24
font_name = pygame.font.get_fonts()[0] 
font = pygame.font.SysFont(font_name, font_size)

faces = [
    [0, 1, 2, 3],
    [4, 5, 6, 7],  
    [0, 1, 5, 4],  
    [1, 2, 6, 5],  
    [2, 3, 7, 6],  
    [3, 0, 4, 7]  
]

direction_vectors = [
    (0, -1, 0), 
    (0, 1, 0),   
    (1, 0, 0),  
    (0, 0, -1),   
    (-1, 0, 0),  
    (-0, 0, 1)   
]

face_colors = [(x,y,z) for x in range(80, 120, 50//len(faces)) for y in range(80, 120, 50//len(faces)) for z in range(80, 120, 50//len(faces))
]

def add_cube(base_x, base_y, base_z, block_points, block_edges, size=200):
    '''Add a cube to the block points and edges list at the specified position'''
    adjusted_base_y = base_y
    cube_position_key = (round(base_x / size) * size, round(adjusted_base_y / size) * size, round(base_z / size) * size)
    
    while cube_position_key in occupied_positions:
        adjusted_base_y += size 
        cube_position_key = (cube_position_key[0], round(adjusted_base_y / size) * size, cube_position_key[2])
    
    base_index = len(block_points)
    
    block_points.extend([
        (base_x + size, adjusted_base_y, base_z + size), (base_x + size, adjusted_base_y, base_z),
        (base_x, adjusted_base_y, base_z), (base_x, adjusted_base_y, base_z + size),
        (base_x + size, adjusted_base_y + size, base_z + size), (base_x + size, adjusted_base_y + size, base_z),
        (base_x, adjusted_base_y + size, base_z), (base_x, adjusted_base_y + size, base_z + size)
    ])
    
    for i in range(4):
        block_edges.append((base_index + i, base_index + (i + 1) % 4))
        block_edges.append((base_index + i + 4, base_index + (i + 1) % 4 + 4))
        block_edges.append((base_index + i, base_index + i + 4))

    occupied_positions.add(cube_position_key)

def is_point_on_screen(point, screen_width, screen_height):
    tolerance = 50
    return -tolerance <= point[0] <= screen_width + tolerance and -tolerance <= point[1] <= screen_height + tolerance

def render_dynamic_ground(camera_pos, yaw, pitch, screen_width, screen_height, fov_rad):
    '''Render the ground squares that are visible to the camera'''
    drawn_squares = 0
    view_distance = render_distance  
    
    num_squares_half_width = view_distance // face_size  

    start_x = (camera_pos[0] // face_size) * face_size - num_squares_half_width * face_size
    end_x = start_x + 2 * num_squares_half_width * face_size
    start_z = (camera_pos[2] // face_size) * face_size - num_squares_half_width * face_size
    end_z = start_z + 2 * num_squares_half_width * face_size
    
    for x in range(int(start_x), int(end_x) + 1, face_size):
        for z in range(int(start_z), int(end_z) + 1, face_size):
            square_corners = [
                (x, 0, z),
                (x + face_size, 0, z),
                (x + face_size, 0, z + face_size),
                (x, 0, z + face_size)
            ]

            projected_corners = [transform_point(*corner, camera_pos, yaw, pitch, screen_width, screen_height, fov_rad) for corner in square_corners]
            
            if None not in projected_corners and any(is_point_on_screen(point, screen_width, screen_height) for point in projected_corners):
                if draw_faces:
                    pygame.draw.polygon(screen, ground_square_color, projected_corners)
                pygame.draw.polygon(screen, ground_square_outline_color, projected_corners, 1)
                drawn_squares += 1
    if debug:
        print(drawn_squares)

def calculate_centroid(vertices, block_points):
    """Calculate the centroid of a face based on its vertices."""
    x = sum(block_points[vertex][0] for vertex in vertices) / len(vertices)
    y = sum(block_points[vertex][1] for vertex in vertices) / len(vertices)
    z = sum(block_points[vertex][2] for vertex in vertices) / len(vertices)
    return (x, y, z)

def calculate_distance(camera_pos, point):
    return ((camera_pos[0] - point[0]) ** 2 + (camera_pos[1] - point[1]) ** 2 + (camera_pos[2] - point[2]) ** 2) ** 0.5

def to_grid_pos(point):
    '''Round a point to the nearest grid position'''
    return (round(point[0] / face_size) * face_size, round(point[1] / face_size) * face_size, round(point[2] / face_size) * face_size)

def render_block_faces(block_points, camera_pos, yaw, pitch, screen_width, screen_height, fov_rad):
    '''Render the faces of the blocks that are visible to the camera'''
    drawn_faces = 0
    faces_with_details = []

    occupied_positions = {to_grid_pos(block_points[i]) for i in range(0, len(block_points), 8)}

    for block_index in range(len(block_points) // 8):
        for i, (face, color) in enumerate(zip(faces, face_colors)):
            if i == 0 and to_grid_pos(block_points[block_index * 8])[1] == 0:
                continue
            centroid = calculate_centroid([vertex + block_index * 8 for vertex in face], block_points)
            distance = calculate_distance(camera_pos, centroid)
            block_position = to_grid_pos(block_points[block_index * 8])

            direction = direction_vectors[i]
            adjacent_position = (
                block_position[0] + direction[0] * face_size,
                block_position[1] + direction[1] * face_size,
                block_position[2] + direction[2] * face_size
            )

            if adjacent_position in occupied_positions:
                continue

            faces_with_details.append((distance, face, color, block_index))

    faces_with_details.sort(reverse=True, key=lambda x: x[0])

    for distance, face, color, block_index in faces_with_details:
        centroid = calculate_centroid([vertex + block_index * 8 for vertex in face], block_points)  
        edge1 = [block_points[block_index * 8 + face[1]][i] - block_points[block_index * 8 + face[0]][i] for i in range(3)]  
        edge2 = [block_points[block_index * 8 + face[2]][i] - block_points[block_index * 8 + face[0]][i] for i in range(3)]  
        normal = cross_product(edge1, edge2)
        
        view_vector = [centroid[i] - camera_pos[i] for i in range(3)]
        
        if dot_product(normal, view_vector) < 0:
            projected_face = [transform_point(*block_points[vertex], camera_pos, yaw, pitch, screen_width, screen_height, fov_rad) for vertex in [vertex + block_index * 8 for vertex in face]]
            if None not in projected_face and any(is_point_on_screen(point, screen_width, screen_height) for point in projected_face):
                if draw_faces:
                    pygame.draw.polygon(screen, color, projected_face)
                pygame.draw.polygon(screen, (0, 0, 0), projected_face, 1)
                drawn_faces += 1
    if debug:
        print(drawn_faces)

def dot_product(v1, v2):
    '''Calculate the dot product of two vectors'''
    return sum(v1[i] * v2[i] for i in range(3))

def cross_product(v1, v2):
    '''Calculate the cross product of two vectors'''
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0]
    )

def transform_point(x, y, z, camera_pos, yaw, pitch, screen_width, screen_height, fov_rad):
    '''Transform a 3D point to 2D screen coordinates'''
    x, y, z = to_camera_space(x, y, z, camera_pos)
    x, z = rotate_yaw(x, z, yaw)
    y, z = rotate_pitch(y, z, pitch)

    if near_clip_z(z) or far_clip_z(z):
        return None
    
    x_screen, y_screen = project_to_screen(x, y, z, screen_width, screen_height, fov_rad)

    return int(x_screen), int(y_screen)

def project_to_screen(x, y, z,screen_width, screen_height, fov_rad):
    '''Project a 3D point to 2D screen coordinates'''
    x_proj = (fov_rad * x) / z
    y_proj = (fov_rad * y) / z
    
    x_proj *= (screen_height / screen_width)
    
    x_screen = (x_proj + 1) * screen_width / 2
    y_screen = (1 - y_proj) * screen_height / 2

    return int(x_screen), int(y_screen)

def near_clip_z(z):
    if z < near_clip:
        return True
    return False

def far_clip_z(z):
    if z > far_clip: 
        return True
    return False

def to_camera_space(x, y, z, camera_pos):
    '''Convert point to camera space'''
    x -= camera_pos[0]
    y -= camera_pos[1]
    z -= camera_pos[2]
    return x, y, z

def rotate_yaw(x, z, yaw):
    '''Rotate the point around the yaw axis'''
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    
    new_x = cos_yaw * x + sin_yaw * z
    new_z = cos_yaw * z - sin_yaw * x
    return new_x, new_z

def rotate_pitch(y, z, pitch):
    '''Rotate the point around the pitch axis'''
    cos_pitch = math.cos(pitch)
    sin_pitch = math.sin(pitch)
    
    new_y = cos_pitch * y - sin_pitch * z
    new_z = cos_pitch * z + sin_pitch * y
    return new_y, new_z


def place_block():
    '''Place a block in front of the camera'''
    forward_x = math.sin(-yaw)
    forward_z = math.cos(-yaw)
    block_distance = 400  

    block_x = camera_pos[0] + forward_x * block_distance
    block_z = camera_pos[2] + forward_z * block_distance
    block_y = 0 
    
    block_x = round(block_x / face_size) * face_size
    block_z = round(block_z / face_size) * face_size

    add_cube(block_x, block_y, block_z, block_points, block_edges)

def lerp(start, end, factor):
    return start + (end - start) * factor

def draw_cursor():
    pygame.draw.circle(screen, WHITE, (screen_width // 2, screen_height // 2), 3)

def move_camera(delta_x, delta_z, camera_pos, yaw):
    forward_x = math.sin(yaw) * delta_z
    forward_z = math.cos(yaw) * delta_z
    strafe_x = math.sin(yaw + math.pi / 2) * delta_x
    strafe_z = math.cos(yaw + math.pi / 2) * delta_x
    
    camera_pos[0] += forward_x + strafe_x
    camera_pos[2] += forward_z + strafe_z

running = True
last_time = pygame.time.get_ticks()
while running:
    now = pygame.time.get_ticks()
    delta_time = (now - last_time) / 1000.0
    last_time = now
    for event in pygame.event.get():
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            place_block()
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            draw_faces = not draw_faces
        elif event.type == pygame.VIDEORESIZE: 
            screen_width, screen_height = event.size
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)

    keys = pygame.key.get_pressed()
    delta_x = 0
    delta_z = 0

    if keys[pygame.K_w]:
        delta_z = player_movement_speed * delta_time
    if keys[pygame.K_s]:
        delta_z = -player_movement_speed * delta_time
    if keys[pygame.K_a]:
        delta_x = -strafe_speed * delta_time
    if keys[pygame.K_d]:
        delta_x = strafe_speed * delta_time
    if keys[pygame.K_SPACE]:
        target_pos[1] += player_movement_speed * delta_time
    if keys[pygame.K_LSHIFT]:
        target_pos[1] -= player_movement_speed * delta_time
        if target_pos[1] <= player_height:
            target_pos[1] = player_height

    if delta_x != 0 and delta_z != 0:
        factor = 1 / math.sqrt(2)
        delta_x *= factor
        delta_z *= factor

    if delta_x != 0 or delta_z != 0:
        move_camera(delta_x, delta_z, target_pos, -yaw)
    
    for i in range(3):
        camera_pos[i] = lerp(camera_pos[i], target_pos[i], player_movement_smooth)

    mx, my = pygame.mouse.get_rel()
    target_yaw -= mx * camera_speed
    target_pitch -= my * camera_speed
    target_pitch = max(-math.pi / 2.2, min(math.pi / 2.2, target_pitch))

    yaw = lerp(yaw, target_yaw, camera_lerp_factor)
    pitch = lerp(pitch, target_pitch, camera_lerp_factor)

    screen.fill((135, 206, 235))
    render_dynamic_ground(camera_pos, yaw, pitch, screen_width, screen_height, fov_rad) 
    render_block_faces(block_points, camera_pos, yaw, pitch, screen_width, screen_height, fov_rad)

    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps:.2f}", True, RED)
    screen.blit(fps_text, (10, 10))  
    draw_cursor()
    pygame.display.flip() 
    clock.tick(144)  

pygame.quit()
