-- Rooms Table
CREATE TABLE public.rooms (
    id SERIAL PRIMARY KEY,
    code VARCHAR(5) UNIQUE NOT NULL,
    name TEXT NOT NULL,
    host TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on room code for faster lookups
CREATE INDEX rooms_code_idx ON public.rooms(code);

-- Pending Users Table
CREATE TABLE public.pending_users (
    id SERIAL PRIMARY KEY,
    room_code VARCHAR(5) REFERENCES public.rooms(code) ON DELETE CASCADE,
    username TEXT NOT NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(room_code, username)
);

-- Room Users Table
CREATE TABLE public.room_users (
    id SERIAL PRIMARY KEY,
    room_code VARCHAR(5) REFERENCES public.rooms(code) ON DELETE CASCADE,
    username TEXT NOT NULL,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(room_code, username)
);

-- Messages Table
CREATE TABLE public.messages (
    id SERIAL PRIMARY KEY,
    room_code VARCHAR(5) REFERENCES public.rooms(code) ON DELETE CASCADE,
    username TEXT NOT NULL,
    message TEXT NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on room_code and sent_at for faster message retrieval
CREATE INDEX messages_room_sent_idx ON public.messages(room_code, sent_at);

-- Enable Row Level Security (RLS)
ALTER TABLE public.rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pending_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.room_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Create policies (for demonstration purposes - adjust according to your security needs)
-- Allow public access for this demo application
CREATE POLICY "Public access" ON public.rooms FOR ALL USING (true);
CREATE POLICY "Public access" ON public.pending_users FOR ALL USING (true);
CREATE POLICY "Public access" ON public.room_users FOR ALL USING (true);
CREATE POLICY "Public access" ON public.messages FOR ALL USING (true);

-- Setup Realtime
BEGIN;
  -- Enable the realtime extension
  CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
  
  -- Configure realtime for our tables
  COMMENT ON TABLE public.rooms IS 'realtime';
  COMMENT ON TABLE public.pending_users IS 'realtime';
  COMMENT ON TABLE public.room_users IS 'realtime';
  COMMENT ON TABLE public.messages IS 'realtime';
COMMIT;
