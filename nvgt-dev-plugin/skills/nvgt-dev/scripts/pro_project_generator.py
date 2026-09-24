import os
import sys

# NVGT Pro-Project Generator v1.0
# Scaffolds a high-fidelity, modular NVGT project in one-shot.

dirs = [
    "sounds",
    "sounds/music",
    "sounds/sfx",
    "data",
    "include",
    "build"
]

main_script = """#include "menu.nvgt"
#include "sound_pool.nvgt"

// --- Global Engine Core ---
class game_engine {
    menu m;
    sound_pool p;
    bool running = true;
    
    game_engine() {
        // Initialization Logic
        p.update_listener_3d(0, 0, 0); // Start at origin
    }
    
    void run() {
        show_main_menu();
        while(running) {
            wait(5); // Prevent main thread freezing
            // Global controller loop
        }
    }
    
    void show_main_menu() {
        m.reset(true);
        m.add_item("Start Game", "start");
        m.add_item("Exit", "exit");
        
        while(m.monitor()) {
            wait(5);
        }
        
        if(m.selected_item_id == "start") {
            start_gameplay();
        } else {
            running = false;
        }
    }
    
    void start_gameplay() {
        speak("Game started.");
        // Gameplay loop
    }
}

void main() {
    game_engine game;
    game.run();
}
"""

def scaffold(project_name):
    if not os.path.exists(project_name):
        os.makedirs(project_name)
    
    os.chdir(project_name)
    print(f"--- Scaffolding Professional Project: {project_name} ---")
    
    for d in dirs:
        if not os.path.exists(d):
            os.makedirs(d)
            print(f"Created directory: {d}")
            
    with open("main.nvgt", "w") as f:
        f.write(main_script)
        print("Created main.nvgt (Pro-Engine Boilerplate)")
        
    print(f"Done! Ready to build '{project_name}' like a pro.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pro_project_generator.py <project_name>")
    else:
        scaffold(sys.argv[1])
