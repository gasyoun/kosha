<?php
/**
 * Plugin Name: kosha brand proxy
 * Description: Intercept /health /ready /metrics /api /dicts /w and proxy to kosha on .92.
 */
if (!defined('ABSPATH')) {
    exit;
}
$path = parse_url($_SERVER['REQUEST_URI'] ?? '', PHP_URL_PATH) ?: '';
if (preg_match('#^/(health|ready|metrics)/?$|^/(api|dicts|w)/#', $path)) {
    require ABSPATH . 'kosha/proxy.php';
    exit;
}
