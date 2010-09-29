//---------------------------------------------------
// Name: OpenNero : Log
// Desc:  logs information
//---------------------------------------------------

#include "core/Common.h"
#include "Log.h"
#include "LogConnections.h"
#include "scripting/scriptIncludes.h"
#include <vector>
#include <iostream>

namespace OpenNero
{
	namespace Log
	{
		static ILogConnectionVector sLogConnections;
        static FilterList           sFilterList;

        /// helper utility functions
        namespace LogUtil
        {
            /**
             * Find a given log connection by its name
             * @param connectionName the connection to search for
             * @return a shared ptr to the connection, NULL if none found
            */
            ILogConnectionPtr find( const std::string& connectionName )
            {
                ILogConnectionVector::iterator itr = sLogConnections.begin();
                for( ; itr != sLogConnections.end(); ++itr )
                    if( (*itr)->getConnectionName() == connectionName )
                        return *itr;

                return ILogConnectionPtr();
            }

            /// define a pointer to member method of ILogConnection
            typedef void (ILogConnection::*MemberLogFunc)( const char* msg );

            /// output a message to a member method of ILogConnection on an instance of ILogConnection
            /// @param func the member function to call
            /// @param msgType the type of message
            /// @param connectionName the name of the connection
            /// @param msg the message to output
            void OutputToLogFunc( MemberLogFunc func, const char* msgType, const char* connectionName, const char* msg )
            {
                if( msgType )
                {
                    // if the message type is in the filter list, then ignore it
                    // if we do not contain the 'all' receiver or the msgType receiver, exit
                    if( std::find( sFilterList.begin(), sFilterList.end(), msgType )   != sFilterList.end() )
                    {
                        return;
                    }
                }

                // if the connectionName is null, broadcast to all
                if( !connectionName )
                {
                    ILogConnectionVector::iterator itr = sLogConnections.begin();
			        ILogConnectionVector::iterator end = sLogConnections.end();

			        for( ; itr != end; ++itr )
			        {
                        Assert( *itr );

                        // Ok, this line looks complicated.
                        // 1) Get a reference to the ILogConnection instance
                        // 2) Call a member method on it with the provided member method pointer
                        // 3) Pass msg to that method
                        ((*(*itr)).*func)(msg);
			        }
                }

                // if the connectionName is valid, output to that connection
                else
                {
                    if( ILogConnectionPtr c = LogUtil::find(connectionName) )
                    {
                        ((*c).*func)(msg);
                    }
                }
            }
        }

		/**
		 * Add a connection to our manager. Increment the ref count on conn
		 * @param conn a log connection to add
	    */
		void AddLogConnection( ILogConnectionPtr conn )
		{
			if(conn)
			{
				sLogConnections.push_back(conn);
			}
		}

		/**
		 * Remove a connection from our manager. Decrement the ref count on conn
		 * @param conn a log connection to remove
	    */
		void RemoveLogConnection( ILogConnectionPtr conn )
		{
            std::remove( sLogConnections.begin(), sLogConnections.end(), conn );
		}

        /// Log a debug message
        /// @param type the type of message to communicate
        /// @param connectionName the target connection name, if NULL broadcast to all
        /// @param msg the message to log
        void LogDebug( const char* type, const char* connectionName, const char* msg )
        {
            LogUtil::OutputToLogFunc( &ILogConnection::LogDebug, type, connectionName, msg );
        }

        /// Log a normal message
        /// @param type the type of message to communicate
        /// @param connectionName the target connection name, if NULL broadcast to all
        /// @param msg the message to log
        void LogMsg( const char* type, const char* connectionName, const char* msg )
        {
            LogUtil::OutputToLogFunc( &ILogConnection::LogMsg, type, connectionName, msg );
        }

        /// Log a warning message
        /// @param type the type of message to communicate
        /// @param connectionName the target connection name, if NULL broadcast to all
        /// @param msg the message to log
        void LogWarning( const char* type, const char* connectionName, const char* msg )
        {
            LogUtil::OutputToLogFunc( &ILogConnection::LogWarning, type, connectionName, msg );
        }

        /// Log an error message
        /// @param type the type of message to communicate
        /// @param connectionName the target connection name, if NULL broadcast to all
        /// @param msg the message to log
        void LogError( const char* type, const char* connectionName, const char* msg )
        {
            LogUtil::OutputToLogFunc( &ILogConnection::LogError, type, connectionName, msg );
        }

        /// Setup the log system by adding a file log and a console log
		void LogSystemInit()
		{
            // initialize the connections
            ILogConnectionPtr fileLog( new FileStreamConnection( "nero_file_log", "nero_log.txt") );
            ILogConnectionPtr stdioLog( new StreamLogConnection<std::ostream>( "console_log", &std::cout ) );

			AddLogConnection(fileLog);
            AddLogConnection(stdioLog);
		}

        /// Set the list of filters we want to ignore
        void LogSystemSpecifyFilters( const FilterList& flist )
        {
            sFilterList = flist;
        }

        /// clear all the log connections
		void LogSystemShutdown()
		{
			sLogConnections.clear();
		}

#if NERO_TEST
        // This method just tests if the logger will compile, not a functionality test.
        void LogCompileTest()
        {
            LOG_DEBUG_EVERY(5,"Hello");
            LOG_DEBUG("Hello");
            LOG_ERROR("Hello");
            LOG_MSG("Hello");
            LOG_WARNING("Hello");

            LOG_D_DEBUG("file","Hello");
            LOG_D_ERROR("file","Hello");
            LOG_D_MSG("file","Hello");
            LOG_D_WARNING("file","Hello");

            LOG_F_DEBUG("generic","Hello");
            LOG_F_ERROR("generic","Hello");
            LOG_F_MSG("generic","Hello");
            LOG_F_WARNING("generic","Hello");

            LOG_FD_DEBUG("generic","test","Hello");
            LOG_FD_ERROR("generic","test","Hello");
            LOG_FD_MSG("generic","test","Hello");
            LOG_FD_WARNING("generic","test","Hello");
        }
#endif // end NERO_TEST

	} // end Log

    /// log a debugging message from Python
    void py_log_debug(const std::string& msg)
    {
        LOG_F_DEBUG("python", msg);
    }

    /// log a message from Python
    void py_log_msg(const std::string& msg)
    {
        LOG_F_MSG("python", msg);
    }

    /// log a warning message from Python
    void py_log_warning(const std::string& msg)
    {
        LOG_F_WARNING("python", msg);
    }

    /// log an error message from Python
    void py_log_error(const std::string& msg)
    {
        LOG_F_ERROR("python", msg);
    }

    PYTHON_BINDER(LogBinder)
    {
        def("log_message",&py_log_msg, "print a message to the log");
        def("log_warn",&py_log_warning, "print a warning message to the log");
        def("log_debug",&py_log_debug, "print a debugging message to the log");
        def("log_error",&py_log_error, "print an error message to the log");
    }

} //end OpenNero