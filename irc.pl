#!/usr/bin/perl

use warnings;
use strict;

use LWP::UserAgent;
use JSON;
use Mojo::DOM;

package UppercaseBot;
use base qw(Bot::BasicBot);

sub said {
    my $self = shift;
    my $arguments = shift;

    my $body = $arguments->{body};

    # if message startswith !jamesbot
    if ($body =~ /^\!jamesbot/) {
        my $prompt = $body;
        $prompt =~ s/^\!jamesbot //;
        # make http request to https://jamesg.blog/bot/query form encoded with argument prompt=
        my $ua = LWP::UserAgent->new;
        my $response = $ua->post('https://jamesg.blog/bot/query', [query => $prompt]);
        my $json = JSON->new;
        my $data = $json->decode($response->decoded_content);
        my $answer = $data->{response};

        # remove all text in ()
        $answer =~ s/\(.*?\)//g;

        # remove all html tags
        $answer =~ s/<[^>]*>//g;

        $self->say(channel => $arguments->{channel}, body => $answer);
    }
}

package main;

my $bot = UppercaseBot->new(
    server      => "irc.libera.chat",
    port        => "6667",
    channels    => ["#channel"],
    nick        => "bot",
    name        => "bot"
);

$bot->run();