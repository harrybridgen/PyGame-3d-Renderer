import pygame
import math

pygame.init()
screenWidth = 1600
screenHeight = screenWidth // 16 * 9
screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)
pygame.display.set_caption("3D Test")
clock = pygame.time.Clock()
pygame.mouse.set_visible(False)
pygame.event.set_grab(True)
pygame.font.init() 

debug = False

WHITE = (255, 255, 255)
RED = (255, 0, 0)
ground_square_color = (10, 180, 10) 
ground_square_outline_color = (20, 150, 20)  

grid_points = []
grid_edges = []
grid_size = 4000 
square_size = 200

block_points = []
block_edges = []

occupied_positions = set()
player_height = 500
camera_pos = [1000, player_height, -1000]  
yaw, pitch = 0, -0.1 
fov = 70
near_clip = 100
far_clip = grid_size
smooth_factor = 0.3 
target_yaw, target_pitch = yaw, pitch
target_pos = list(camera_pos)
movement_speed = 1200
strafe_speed = movement_speed *0.8
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

def is_point_on_screen(point, screenWidth, screenHeight):
    tolerance = 50
    return -tolerance <= point[0] <= screenWidth + tolerance and -tolerance <= point[1] <= screenHeight + tolerance

def render_dynamic_ground(camera_pos, yaw, pitch, screenWidth, screenHeight, fov):
    drawn_squares = 0
    view_distance = grid_size  
    
    num_squares_half_width = view_distance // square_size  

    start_x = (camera_pos[0] // square_size) * square_size - num_squares_half_width * square_size
    end_x = start_x + 2 * num_squares_half_width * square_size
    start_z = (camera_pos[2] // square_size) * square_size - num_squares_half_width * square_size
    end_z = start_z + 2 * num_squares_half_width * square_size
    
    for x in range(int(start_x), int(end_x) + 1, square_size):
        for z in range(int(start_z), int(end_z) + 1, square_size):
            square_corners = [
                (x, 0, z),
                (x + square_size, 0, z),
                (x + square_size, 0, z + square_size),
                (x, 0, z + square_size)
            ]

            projected_corners = [transform_point(*corner, camera_pos, yaw, pitch, screenWidth, screenHeight, fov) for corner in square_corners]
            
            if None not in projected_corners and any(is_point_on_screen(point, screenWidth, screenHeight) for point in projected_corners):
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
    return (round(point[0] / square_size) * square_size, round(point[1] / square_size) * square_size, round(point[2] / square_size) * square_size)

def render_block_faces(block_points, camera_pos, yaw, pitch, screenWidth, screenHeight, fov):
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
                block_position[0] + direction[0] * square_size,
                block_position[1] + direction[1] * square_size,
                block_position[2] + direction[2] * square_size
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
        
        if sum(normal[i] * view_vector[i] for i in range(3)) < 0:
            projected_face = [transform_point(*block_points[vertex], camera_pos, yaw, pitch, screenWidth, screenHeight, fov) for vertex in [vertex + block_index * 8 for vertex in face]]
            if None not in projected_face and any(is_point_on_screen(point, screenWidth, screenHeight) for point in projected_face):
                pygame.draw.polygon(screen, color, projected_face)
                pygame.draw.polygon(screen, (0, 0, 0), projected_face, 1)
                drawn_faces += 1
    if debug:
        print(drawn_faces)


def project_3d(x, y, z, screen_width, screen_height, fov):
    if z < near_clip: 
        return None
    
    if z > far_clip:
        return None
    
    x_proj = (fov_rad * x) / z
    y_proj = (fov_rad * y) / z
    

    x_proj *= (screen_height / screen_width)
    
    x_screen = (x_proj + 1) * screen_width / 2
    y_screen = (1 - y_proj) * screen_height / 2

    return int(x_screen), int(y_screen)


def cross_product(v1, v2):
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0]
    )

def transform_point(x, y, z, camera_pos, yaw, pitch, screenWidth, screenHeight, fov):
    x -= camera_pos[0]
    y -= camera_pos[1]
    z -= camera_pos[2]
    
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    
    temp_xz = cos_yaw * x + sin_yaw * z
    temp_xy = cos_yaw * z - sin_yaw * x
    x = temp_xz
    z = temp_xy

    cos_pitch = math.cos(pitch)
    sin_pitch = math.sin(pitch)
    
    temp_yz = cos_pitch * y - sin_pitch * z
    temp_yx = cos_pitch * z + sin_pitch * y
    y = temp_yz
    z = temp_yx
    
    return project_3d(x, y, z, screenWidth, screenHeight, fov)

def place_block():
    forward_x = math.sin(-yaw)
    forward_z = math.cos(-yaw)
    block_distance = 400  

    block_x = camera_pos[0] + forward_x * block_distance
    block_z = camera_pos[2] + forward_z * block_distance
    block_y = 0 
    
    block_x = round(block_x / square_size) * square_size
    block_z = round(block_z / square_size) * square_size

    add_cube(block_x, block_y, block_z, block_points, block_edges)

def lerp(start, end, factor):
    return start + (end - start) * factor

def draw_cursor():
    pygame.draw.circle(screen, WHITE, (screenWidth // 2, screenHeight // 2), 3)

def move_camera(delta_x, delta_z, camera_pos, yaw):
    forward_x = math.sin(yaw) * delta_z
    forward_z = math.cos(yaw) * delta_z
    strafe_x = math.sin(yaw + math.pi / 2) * delta_x
    strafe_z = math.cos(yaw + math.pi / 2) * delta_x
    
    camera_pos[0] += forward_x + strafe_x
    camera_pos[2] += forward_z + strafe_z

offset = len(block_points)
block_points.extend(grid_points)
block_edges.extend([(start + offset, end + offset) for start, end in grid_edges])

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
        elif event.type == pygame.VIDEORESIZE: 
            screenWidth, screenHeight = event.size
            screen = pygame.display.set_mode((screenWidth, screenHeight), pygame.RESIZABLE)

    keys = pygame.key.get_pressed()
    delta_x = 0
    delta_z = 0

    if keys[pygame.K_w]:
        delta_z = movement_speed * delta_time
    if keys[pygame.K_s]:
        delta_z = -movement_speed * delta_time
    if keys[pygame.K_a]:
        delta_x = -strafe_speed * delta_time
    if keys[pygame.K_d]:
        delta_x = strafe_speed * delta_time
    if keys[pygame.K_SPACE]:
        target_pos[1] += movement_speed * delta_time
    if keys[pygame.K_LSHIFT]:
        target_pos[1] -= movement_speed * delta_time
        if target_pos[1] <= player_height:
            target_pos[1] = player_height

    if delta_x != 0 and delta_z != 0:
        factor = 1 / math.sqrt(2)
        delta_x *= factor
        delta_z *= factor

    if delta_x != 0 or delta_z != 0:
        move_camera(delta_x, delta_z, target_pos, -yaw)
    
    for i in range(3):
        camera_pos[i] = lerp(camera_pos[i], target_pos[i], smooth_factor)

    mx, my = pygame.mouse.get_rel()
    target_yaw -= mx * 0.001
    target_pitch -= my * 0.001
    target_pitch = max(-math.pi / 2.2, min(math.pi / 2.2, target_pitch))

    yaw = lerp(yaw, target_yaw, smooth_factor)
    pitch = lerp(pitch, target_pitch, smooth_factor)

    screen.fill((135, 206, 235))
    render_dynamic_ground(camera_pos, yaw, pitch, screenWidth, screenHeight, fov) 
    render_block_faces(block_points, camera_pos, yaw, pitch, screenWidth, screenHeight, fov)

    fps = clock.get_fps()
    fps_text = font.render(f"FPS: {fps:.2f}", True, RED)
    screen.blit(fps_text, (10, 10))  
    draw_cursor()
    pygame.display.flip() 
    clock.tick(144)  

pygame.quit()
