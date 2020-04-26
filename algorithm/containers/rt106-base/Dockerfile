ARG BASE_IMAGE
FROM ${BASE_IMAGE}

### for rt106 base image

# install dependencies
RUN pip3 install --upgrade pip && hash -r \
    && pip3 install flask pika boto3 requests junit-xml pytest-cov \
    && pip3 install --upgrade setuptools

# install SDK
ADD rt106GenericAdaptorSQS.py rt106GenericAdaptorAMQP.py rt106GenericAdaptorREST.py rt106SpecificAdaptorCode.py rt106SpecificAdaptorDefinitions.json entrypoint.sh testGenericAdaptorAPIs.py testGenericAdaptorAMQP.py /rt106/

# configure folder structures
RUN mkdir /rt106/input && mkdir /rt106/output && mkdir /rt106/test

# set permissions
RUN chmod a+x /rt106/entrypoint.sh

# set the working directory
WORKDIR /rt106

# establish the user
# create non-privileged user and group
RUN groupadd -r rt106 && useradd -r -g rt106 rt106 && chown -R rt106:rt106 /rt106
USER rt106:rt106

# configure the default port for an analytic, can be overridden in entrypoint
EXPOSE 7106

# entry point
CMD ["/rt106/entrypoint.sh"]

### end rt106


# Enable the dynamic setting of the user
#USER root:root
#COPY provision_container.sh /usr/local/bin/
#RUN chmod 1777 /usr/local/bin/provision_container.sh


#ENTRYPOINT ["/usr/local/bin/provision_container.sh"]
#CMD ["/bin/bash"]

#ARG BUILD_DATE
#ARG VCS_REF
#ARG VCS_URL
#LABEL org.label-schema.vendor="THRIVE Team" \
#      org.label-schema.build-date=$BUILD_DATE \
#      org.label-schema.vcs-url=$VCS_URL \
#      org.label-schema.vcs-ref=$VCS_REF \
#      org.label-schema.schema-version="1.0.0-rc1"
