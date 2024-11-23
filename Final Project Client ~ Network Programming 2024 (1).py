# -*- coding: utf-8 -*-
"""

Created on Fri Nov 15 16:14:23 2024


@author: Isabella Crowe & Raymi Vargas
Univeristy: Wentworth Istitute of Technology
Professor: Salem Othman
Final Project: Super Chat Room

"""

import tkinter as tk
from tkinter import filedialog, scrolledtext, simpledialog
from PIL import Image, ImageTk
import os
import socket
import threading
import base64
import io
import ctypes

class ChatApp:
    def __init__(self, host, port):
        # Connections
        
        # Ask user for their username:
        self.username = simpledialog.askstring("Enter Username", "Please enter your username:")
        
        # Create socket
        self.server_ip = host
        self.server_port = port
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_ip, self.server_port))

        # Create the main window
        self.root = tk.Tk()
        self.root.title(f"SuperChat - {self.username}")
        self.root.configure(bg="lightblue")
        self.root.geometry("575x500")
        
        # Add app icon to the GUI window and to the Windows 11 taskbar app display.
        # Icon had to be converted from .png to .ico
        self.root.iconbitmap('sclogo.ico') #File path of icon
        myappid = 'company.superchat.version'  # Custom app ID for taskbar
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid) #Tethers icon
        self.frame = tk.Frame(self.root) 
        self.frame.pack(padx=10, pady=10)

        # Add widgets
        self.chat_label = tk.Label(self.root, text=f"Super Chat \n{self.username}: ", bg="white", font=("Helvetica", 8))
        self.logout_button = tk.Button(self.root, text="Logout", command=self.logout, font=("Helvetica", 10), fg="red")
        self.chat_area = scrolledtext.ScrolledText(self.root, state='disabled')
        self.msg_label = tk.Label(self.root, text="Message: ", bg="white", font=("Helvetica", 12))
        self.input_area = tk.Text(self.root, height=3)
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message, font=("Helvetica", 12))
        self.plus_button = tk.Button(self.root, text="+", command=self.open_image, font=("Helvetica", 16), width=2, fg = "red" )
        self.logout_button.place(relx=0.85, rely=0.02, relwidth=0.1)  # Top-right corner
        self.chat_label.place(relx=0.25, rely=0.05, relwidth=0.5)     # Centered and reduced width
        self.chat_area.place(relx=0.1, rely=0.15, relwidth=0.8, relheight=0.5)
        self.plus_button.place(relx=0.02, rely=0.15, relwidth=0.05, relheight=0.05)  # Left side of the text_area
        self.msg_label.place(relx=0.1, rely=0.7, relwidth=0.8)
        self.input_area.place(relx=0.25, rely=0.75, relwidth=0.5, relheight=0.1)  # Centered and set to 50% width
        self.send_button.place(relx=0.8, rely=0.9, relwidth=0.15)
        
        
        # Establish background threads for messages
        # Deamon threads exit as soon as the main program is completed
        self.root.bind('<Return>', lambda event: self.send_message())
        self.root.bind("<Configure>", self.resize)
        threading.Thread(target=self.receive, daemon=True).start()

        self.root.mainloop() # Main loop in which the GUI is mantain and run

    def resize(self, event):
        # Adjust widget positions on window resize
        # Calculate new sizes based on 80% of the window's width and height
        # Sizes are relatives
        # If the windows is 1000 X 1000 pixels  wide then elements will be spread 800 pixels across
        self.chat_label.place_configure(relx=0.25, rely=0.05, relwidth=0.5)
        self.logout_button.place_configure(relx=0.85, rely=0.02, relwidth=0.1)
        self.chat_area.place_configure(relwidth=0.8, relheight=0.5, relx=0.1)
        self.plus_button.place_configure(relx=0.15, rely=0.77, relwidth=0.08, relheight=0.05)
        self.msg_label.place_configure(relwidth=0.8, relx=0.1)
        self.input_area.place_configure(relwidth=0.5, relx=0.25)
        self.send_button.place_configure(relx=0.8, relwidth=0.15)


    def open_image(self):
        
        # Prompts the user to select image
        # filedialong.askopenfilename function opens operating system's File Explorer
        # The user must select input from File Explorer.
        file_path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Open Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.gif")]
        )
        if file_path:
            
            # Sends image to the server
            self.send_image(file_path)

    def send_message(self):
        message = self.input_area.get("1.0", 'end').strip()
        if message:
            self.chat_area.configure(state='normal')
            
            # Show text message to send in the main window.
            self.chat_area.configure(state='disabled')
            self.chat_area.yview('end')
            self.input_area.delete("1.0", 'end')
            self.send_text(message)

    def send_text(self, message):
        message_data = f"{self.username}: {message}"
        self.sock.send(message_data.encode('ascii'))

    def resize_image(self,image_path, max_size=(500, 500)):
        img = Image.open(image_path)
        
        # Scaling image
        # LANCZOS function is a advanced technique to interpolate digital signals
        # LANCZOS applied process renders images better, offering better quaility and simplicity.
        img.thumbnail(max_size, Image.LANCZOS)  
        return img

    def send_image(self, image_path):
        try:
            # Applies proper image scaling and format
            resized_img = self.resize_image(image_path)
            img_byte_arr = io.BytesIO()
            resized_img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Encode image process
            # The image is paritioned into different pieces (packets) for transmission
            # Each packet is formed by each piece being encapsulated into a header and chunk.
            # Header contains the routing information of the packet. (50 bytes)
            # Chunk is the actual data of the image being transmitted carried within the packet. (978 bytes)
            # Header and chunk re joined together to form the actual stream of data been transmitted (packet)
            # The formed packet is then encoded and sent off
            # NOTE: Each packet is 1028 bytes
            
            encoded_image = base64.b64encode(img_byte_arr).decode('ascii')
            total_parts = (len(encoded_image) + PART_SIZE - 1) // PART_SIZE
            for i in range(total_parts):
                chunk = encoded_image[i * PART_SIZE:(i + 1) * PART_SIZE]
                header = f"IMAGE:{self.username}:{i}:{total_parts}:"
                header = header = header.rjust(HEADER_SIZE, ' ')
                self.sock.send((header + chunk).encode('ascii'))

            print("Image sent in chunks successfully!")
        except Exception as e:
            print(f"Error while sending image: {e}")



    def receive(self):
        image_chunks = {}  
        expected_chunks = {}  

        while self.running:
            try:
                # Decoding image process.
                message = self.sock.recv(BUFFER_SIZE).decode('ascii')
                print(f"Received message of length: {len(message)}")
                message = message.strip()
                print(f"Received message: {message[:20]}")
                
                # Evaluate if the packet recieve is a text message.
                if message == 'NICK':
                    # Display message process.
                    self.sock.send(self.username.encode('ascii'))
                else:
                    
                    # Evaluate if the packet recieve is a image message
                    if message.startswith('IMAGE:'):
                        # Display image process.
                        parts = message[len('IMAGE:'):].split(":", 3)
                        if len(parts) == 4:
                            # Properly read the image packets recieved
                            nickname, part_num, total_parts, part_data = parts
                            part_num = int(part_num)
                            total_parts = int(total_parts)
                            if nickname not in image_chunks:
                                image_chunks[nickname] = [None] * total_parts
                                expected_chunks[nickname] = total_parts
                            image_chunks[nickname][part_num] = part_data
                            
                            # Join image packets together to create the encoded image text.
                            if None not in image_chunks[nickname]:
                                full_encoded_data = ''.join(image_chunks[nickname])
                                
                                # Display the image
                                # This is done by decoding the encoded image text recieved
                                # Then the image is formed and inserted into the inbox (chat_area)
                                try:
                                    img_data = base64.b64decode(full_encoded_data)
                                    img = Image.open(io.BytesIO(img_data))
                                    img_tk = ImageTk.PhotoImage(img)
                                    image_label = tk.Label(self.chat_area, image=img_tk)
                                    image_label.image = img_tk 
                                    self.chat_area.configure(state='normal')
                                    self.chat_area.insert('end', nickname + ":")
                                    self.chat_area.insert('end', "\n")
                                    self.chat_area.window_create('end', window=image_label)
                                    self.chat_area.insert('end', "\n")
                                    self.chat_area.configure(state='disabled')
                                    self.chat_area.yview('end')
                                    del image_chunks[nickname]
                                    del expected_chunks[nickname]
                                except Exception as e:
                                    print(f"Failed to display image: {e}")
                        else:
                            print("Malformed image message received")
                    else:
                        
                        # Display text message
                        self.chat_area.configure(state='normal')
                        self.chat_area.insert('end', message + '\n')
                        self.chat_area.configure(state='disabled')
                        self.chat_area.yview('end')
            except ConnectionAbortedError:
                print("Connection to server lost.")
                self.sock.close()
                break
    
    # Lougout function for 
    def logout(self):
        self.sock.send(f"{self.username} has logged out.".encode('ascii'))
        self.running = False # Stop running loop
        self.sock.close() # Close connection to server
        self.root.quit() #  Exit the running main loops
        self.root.destroy() # Close the window by destroying all window's widgets
        

# Class public variables
# DO NOT TOUCH UNLESS YOU WANT BAD THINGS TO HAPPEN
if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8081
    BUFFER_SIZE = 1028
    HEADER_SIZE = 50
    PART_SIZE = BUFFER_SIZE - HEADER_SIZE
    app = ChatApp(host=HOST, port=PORT)