// Starts the bot. Without arguments it talks to a referee over stdin/stdout, as on the server;
// with --tcp it connects to a waiting sbm-arena, e.g. from the debugger.
Sbm.Sdk.Run<MyBot.TemplateBot>();
