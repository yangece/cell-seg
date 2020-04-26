FROM thrive20/rt106-algorithm-sdk-focal:latest

USER root

# add the artifacts emitted from the dev container
#ADD rt106-simple-region-growing.tar.gz /rt106/bin

# add the adaptor code specialized for this algorithm
ADD rt106SpecificAdaptorCode.py rt106SpecificAdaptorDefinitions.json entrypoint.sh /rt106/
ADD testDAPISeg.py /rt106/
ADD models /rt106/

RUN mkdir -p /rt106/input && mkdir -p /rt106/output

# set permissions
RUN chown -R rt106:rt106 /rt106

# set the working directory
WORKDIR /rt106

# establish user (created in the base image)
USER rt106:rt106

# configure the default port for an analytic, can be overridden in entrypoint
EXPOSE 7106

# entry point
CMD ["/rt106/entrypoint.sh"]
