using System.Net;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Sbm.Runtime.Remote;

/// <summary>Asks the web API for a remote game (POST /api/v1/remote/matches, E116).</summary>
internal static class GameRequest
{
    internal const string ApiPath = "/api/v1/remote/matches";
    internal const string UserAgent = "schachbotmanager";
    private static readonly TimeSpan Timeout = TimeSpan.FromSeconds(15);

    /// <summary>baseUrl is the site, e.g. https://schachbotmanager.example.org.</summary>
    internal static Seat Request(string baseUrl, string token, JsonObject body)
    {
        if (
            !Uri.TryCreate(baseUrl, UriKind.Absolute, out var uri)
            || (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps)
            || string.IsNullOrEmpty(uri.Host)
        )
        {
            throw new RemoteException(
                $"--remote needs an http or https address, not '{baseUrl}'",
                "usage"
            );
        }
        var path = uri.AbsolutePath.TrimEnd('/');
        var site = $"{uri.Scheme}://{uri.Authority}{path}";
        try
        {
            using var client = new HttpClient { Timeout = Timeout };
            using var request = new HttpRequestMessage(HttpMethod.Post, site + ApiPath)
            {
                Content = new StringContent(body.ToJsonString(), Encoding.UTF8, "application/json"),
            };
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
            request.Headers.Accept.Add(new MediaTypeWithQualityHeaderValue("application/json"));
            request.Headers.Add("X-SBM-CSRF", "1");
            request.Headers.UserAgent.ParseAdd(UserAgent);
            using var response = client.Send(request);
            var answer = Read(response);
            if (!response.IsSuccessStatusCode)
            {
                throw Refused(response.StatusCode, answer);
            }
            var scheme = uri.Scheme == Uri.UriSchemeHttps ? "wss" : "ws";
            return new Seat(
                Text(answer, "match_id"),
                Text(answer, "seat"),
                Text(answer, "color"),
                $"{scheme}://{uri.Authority}{path}{Text(answer, "socket_path")}"
            );
        }
        catch (Exception error)
            when (error
                    is HttpRequestException
                        or TaskCanceledException
                        or IOException
                        or JsonException
                        or KeyNotFoundException
                        or InvalidOperationException
            )
        {
            throw new RemoteException($"cannot reach {baseUrl}: {error.Message}", error);
        }
    }

    /// <summary>The body of the answer, or null if it is not JSON.</summary>
    private static JsonNode? Read(HttpResponseMessage response)
    {
        using var stream = response.Content.ReadAsStream();
        try
        {
            return JsonNode.Parse(stream);
        }
        catch (JsonException) when (!response.IsSuccessStatusCode)
        {
            return null;
        }
    }

    private static RemoteException Refused(HttpStatusCode status, JsonNode? answer)
    {
        if (
            answer is JsonObject error
            && error["code"] is JsonValue code
            && code.TryGetValue(out string? codeText)
            && error["message"] is JsonValue message
            && message.TryGetValue(out string? messageText)
        )
        {
            if (
                error["field"] is JsonValue field
                && field.TryGetValue(out string? fieldText)
                && fieldText.Length > 0
            )
            {
                messageText = $"{fieldText}: {messageText}";
            }
            return new RemoteException(
                $"the server refused the game ({codeText}): {messageText}",
                codeText
            );
        }
        return new RemoteException(
            $"the server refused the game ({RemoteException.Network}): HTTP {(int)status}",
            RemoteException.Network
        );
    }

    private static string Text(JsonNode? answer, string name) =>
        answer?[name] is JsonValue value && value.TryGetValue(out string? text)
            ? text
            : throw new KeyNotFoundException($"the answer has no {name}");
}
