<?php
/**
 * Reverse-proxy allowlisted kosha routes from samskrtam.ru to the
 * live API on 192.168.200.92:8002 (LAN). Fallback: public sslip.
 *
 * Served as /kosha/proxy.php via .htaccess, and required from the
 * mu-plugin. Not a WordPress bootstrap.
 */
declare(strict_types=1);

const KOSHA_UPSTREAMS = [
    'http://192.168.200.92:8002',
    'https://kosha.193.232.229.92.sslip.io',
];

function kosha_path_allowed(string $path): bool
{
    return (bool) preg_match(
        '#^/(health|ready|metrics)/?$|^/(api|dicts|w)/#',
        $path
    );
}

function kosha_proxy(): void
{
    $uri = $_SERVER['REQUEST_URI'] ?? '/';
    $path = parse_url($uri, PHP_URL_PATH) ?: '/';
    $query = parse_url($uri, PHP_URL_QUERY);

    if (!kosha_path_allowed($path)) {
        http_response_code(404);
        header('Content-Type: text/plain; charset=utf-8');
        header('X-Kosha-Proxy: denied');
        echo "not a kosha route\n";
        return;
    }

    $suffix = $path;
    if ($query) {
        $suffix .= '?' . $query;
    }

    $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
    $body = file_get_contents('php://input') ?: '';

    $fwd = [];
    if (!empty($_SERVER['HTTP_X_REQUEST_ID'])) {
        $fwd[] = 'X-Request-ID: ' . $_SERVER['HTTP_X_REQUEST_ID'];
    }
    if (!empty($_SERVER['HTTP_ACCEPT'])) {
        $fwd[] = 'Accept: ' . $_SERVER['HTTP_ACCEPT'];
    }
    $fwd[] = 'X-Forwarded-Proto: https';
    $fwd[] = 'X-Forwarded-Host: samskrtam.ru';

    $last_err = 'no upstream tried';
    foreach (KOSHA_UPSTREAMS as $base) {
        $ch = curl_init($base . $suffix);
        if ($ch === false) {
            $last_err = 'curl_init failed';
            continue;
        }
        $opts = [
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => $fwd,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HEADER => true,
            CURLOPT_TIMEOUT => 60,
            CURLOPT_CONNECTTIMEOUT => 5,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_SSL_VERIFYPEER => true,
        ];
        if ($method === 'HEAD') {
            $opts[CURLOPT_NOBODY] = true;
        } else {
            $opts[CURLOPT_POSTFIELDS] = $body;
        }
        curl_setopt_array($ch, $opts);
        $raw = curl_exec($ch);
        if ($raw === false) {
            $last_err = curl_error($ch);
            curl_close($ch);
            continue;
        }
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $hsz = (int) curl_getinfo($ch, CURLINFO_HEADER_SIZE);
        curl_close($ch);

        $header_blob = substr($raw, 0, $hsz);
        $resp_body = substr($raw, $hsz);
        http_response_code($status > 0 ? $status : 502);
        foreach (preg_split("/\r\n|\n|\r/", $header_blob) as $line) {
            if (strpos($line, ':') === false) {
                continue;
            }
            [$name, $value] = explode(':', $line, 2);
            $lname = strtolower(trim($name));
            if (in_array($lname, [
                'transfer-encoding',
                'connection',
                'keep-alive',
                'content-length',
                'content-encoding',
            ], true)) {
                continue;
            }
            if (in_array($lname, [
                'content-type',
                'x-request-id',
                'cache-control',
                'etag',
            ], true)) {
                header(trim($name) . ':' . $value);
            }
        }
        header('X-Kosha-Proxy: ' . $base);
        echo $resp_body;
        return;
    }

    http_response_code(502);
    header('Content-Type: text/plain; charset=utf-8');
    header('X-Kosha-Proxy: fail');
    echo "kosha upstream unreachable\n";
}

kosha_proxy();
