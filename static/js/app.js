// Initialize socket connection
console.log('Initializing Socket.IO...');
const socket = io({
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 5
});

let currentUser = null;
let typingTimeout = null;

// Socket connection events
socket.on('connect', function() {
  console.log('✅ Socket connected:', socket.id);
});

socket.on('connect_error', function(error) {
  console.error('❌ Socket connection error:', error);
});

socket.on('disconnect', function(reason) {
  console.log('⚠️ Socket disconnected:', reason);
});

// Join chat function
function joinChat() {
  const nicknameInput = document.getElementById('nicknameInput');
  const nickname = nicknameInput.value.trim();
  
  if (!nickname) {
    alert('Please enter a nickname');
    nicknameInput.focus();
    return;
  }
  
  console.log('🚀 Attempting to join with nickname:', nickname);
  socket.emit('join', { nickname: nickname });
}

// Send message function
function sendMessage() {
  const input = document.getElementById('messageInput');
  const text = input.value.trim();
  
  if (!text) {
    console.log('⚠️ Empty message, not sending');
    return;
  }
  
  console.log('📤 Sending message:', text);
  console.log('📤 Current user:', currentUser);
  console.log('📤 Socket connected:', socket.connected);
  
  socket.emit('send_message', { text: text }, function(response) {
    console.log('✅ Message send acknowledged:', response);
  });
  
  input.value = '';
  socket.emit('typing', { typing: false });
}

// Update user list
function updateUserList(users) {
  console.log('👥 Updating user list:', users);
  const list = document.getElementById('userList');
  const count = document.getElementById('userCount');
  
  if (!list || !count) {
    console.error('User list elements not found');
    return;
  }
  
  list.innerHTML = '';
  count.textContent = users.length;
  
  users.forEach(function(u) {
    const li = document.createElement('li');
    li.textContent = u;
    if (u === currentUser) {
      li.classList.add('me');
    }
    list.appendChild(li);
  });
}

// Append message
function appendMessage(nick, text, ts) {
  const list = document.getElementById('messageList');
  if (!list) {
    console.error('Message list not found');
    return;
  }
  
  const div = document.createElement('div');
  div.className = nick === currentUser ? 'message me' : 'message';
  
  const time = new Date(ts * 1000).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });
  
  div.innerHTML = '<strong>' + nick + '</strong><span class="time">' + time + '</span><p>' + text + '</p>';
  list.appendChild(div);
  list.scrollTop = list.scrollHeight;
}

// Append system message
function appendSystemMessage(text) {
  const list = document.getElementById('messageList');
  if (!list) {
    console.error('Message list not found');
    return;
  }
  
  const div = document.createElement('div');
  div.className = 'message system';
  div.textContent = text;
  list.appendChild(div);
  list.scrollTop = list.scrollHeight;
}

// Socket event listeners
socket.on('join_success', function(data) {
  console.log('✅ Join success:', data);
  currentUser = data.nickname;
  
  const myNickname = document.getElementById('myNickname');
  const joinContainer = document.getElementById('joinContainer');
  const chatContainer = document.getElementById('chatContainer');
  const messageInput = document.getElementById('messageInput');
  
  if (myNickname) myNickname.textContent = 'You: ' + currentUser;
  if (joinContainer) joinContainer.style.display = 'none';
  if (chatContainer) chatContainer.style.display = 'flex';
  if (messageInput) messageInput.focus();
});

socket.on('join_error', function(data) {
  console.error('❌ Join error:', data);
  alert(data.error || 'Failed to join chat');
});

socket.on('user_joined', function(data) {
  console.log('👋 User joined:', data.nickname);
  appendSystemMessage(data.nickname + ' joined the chat');
});

socket.on('user_left', function(data) {
  console.log('👋 User left:', data.nickname);
  appendSystemMessage(data.nickname + ' left the chat');
});

socket.on('users_list', function(data) {
  updateUserList(data.users);
});

socket.on('message', function(data) {
  console.log('💬 Message received:', data);
  appendMessage(data.from, data.text, data.timestamp);
});

socket.on('user_typing', function(data) {
  const indicator = document.getElementById('typingIndicator');
  if (!indicator) return;
  
  if (data.typing) {
    indicator.textContent = data.nickname + ' is typing...';
    indicator.style.display = 'block';
  } else {
    indicator.style.display = 'none';
  }
});

// DOM Ready
window.addEventListener('DOMContentLoaded', function() {
  console.log('📄 DOM loaded');
  
  // Join button
  const joinBtn = document.getElementById('joinBtn');
  if (joinBtn) {
    joinBtn.onclick = joinChat;
    console.log('✅ Join button listener attached');
  } else {
    console.error('❌ Join button not found');
  }

  // Nickname input - Enter key
  const nicknameInput = document.getElementById('nicknameInput');
  if (nicknameInput) {
    nicknameInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        joinChat();
      }
    });
    nicknameInput.focus();
    console.log('✅ Nickname input listener attached');
  } else {
    console.error('❌ Nickname input not found');
  }

  // Send button
  const sendBtn = document.getElementById('sendBtn');
  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
    console.log('✅ Send button listener attached');
  }
  
  // Message input
  const messageInput = document.getElementById('messageInput');
  if (messageInput) {
    // Enter key
    messageInput.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });

    // Typing indicator
    messageInput.addEventListener('input', function() {
      if (!currentUser) return;
      
      socket.emit('typing', { typing: true });
      
      clearTimeout(typingTimeout);
      typingTimeout = setTimeout(function() {
        socket.emit('typing', { typing: false });
      }, 1000);
    });
    console.log('✅ Message input listener attached');
  }
  
  console.log('🎉 All event listeners initialized');
});
