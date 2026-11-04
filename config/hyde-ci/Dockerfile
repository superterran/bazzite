FROM mcr.microsoft.com/playwright:v1.64.1-noble
USER root
RUN apt-get update -qq && apt-get install -y --no-install-recommends age curl git gh jq unzip openssh-client libicu74 liblttng-ust1 libkrb5-3 zlib1g && rm -rf /var/lib/apt/lists/*
ARG RUNNER_VERSION=2.338.2
ARG RUNNER_SHA256=baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40
RUN mkdir -p /opt/actions && curl -fsSL "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz" -o /tmp/runner.tar.gz && echo "${RUNNER_SHA256}  /tmp/runner.tar.gz" | sha256sum -c - && tar -xzf /tmp/runner.tar.gz -C /opt/actions && rm /tmp/runner.tar.gz
RUN useradd --uid 10001 --create-home --shell /bin/bash runner
COPY entrypoint.sh /entrypoint.sh
USER 10001:10001
WORKDIR /runner
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENTRYPOINT ["bash", "/entrypoint.sh"]
COPY job-cleanup.sh /opt/job-cleanup.sh
ENV ACTIONS_RUNNER_HOOK_JOB_COMPLETED=/opt/job-cleanup.sh
